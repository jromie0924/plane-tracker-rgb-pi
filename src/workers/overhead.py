from services.adsbTracker import AdsbTrackerService
from services.airlineLookup import AirlineLookupService
from services.databaseManager import DatabaseManager
from services.flightLogic import FlightLogic
from threading import Thread, Lock
from time import sleep
from services.geo import GeoService

import config
import json
import logging
import re

from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import MaxRetryError
from datetime import datetime

from services.trackerLog import TrackerLog


EARTH_RADIUS_M = 6371000  # Earth's radius in m
# BLANK_FIELDS = ["", "N/A", "NONE", "UNKNOWN"]
BLANK_FIELDS: dict = {
  "": 0,
  "N/A": 1,
  "NONE": 2,
  "UNKNOWN": 3
}
NW = 315  # degrees
SE = 135  # degrees

AIRLINE_CODE_REG = r'^(?P<icao>[a-zA-Z]{3}+)+[0-9]*\s*$'

class Overhead:
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self._adsb_api = AdsbTrackerService()
    self._geo_service = GeoService()
    self._airline_lookup = AirlineLookupService()
    self._flight_logic = FlightLogic()
    self._tracker_log = TrackerLog()
    self._database = DatabaseManager()
    self._lock = Lock()
    self._data = []
    self._new_data = False
    self._processing = False
    self.dupe_tracker = {}

  def grab_data(self):
    while not len(self._geo_service.location):
      self.logger.info('Waiting for location data...')
      sleep(1)

    # Rebuild the route database in the background when it's missing or due for a refresh
    if self._database.needs_rebuild():
      db_thread = Thread(target=self._database.rebuild)
      db_thread.daemon = True
      db_thread.start()

    with self._lock:
      if self._processing:
        return
      
      # Mark the current data as old
      self._new_data = False
      self._processing = True

    t = Thread(target=self._grab_data)
    t.daemon = True
    t.start()
  
  @staticmethod
  def tokenize_airline_code_from_callsign(callsign: str) -> str:
    result = re.match(AIRLINE_CODE_REG, callsign)
    icao = result.group('icao') if result else ''
    return icao
      

  def _grab_data(self):
    data = []

    # Grab flight details
    try:
      try:
        flights = self._adsb_api.get_nearby_flights(self._geo_service.latitude, self._geo_service.longitude, config.RADIUS)
      except TimeoutError:
        self.logger.warning("Timeout experienced when getting nearby flights.", exc_info=True)
        flights = None

      if not flights or len(flights) == 0:
        with self._lock:
          self._new_data = False
          self._processing = False
          self._data = []
        sleep(0.1)
        return

      tracker_log_thread = Thread(target=self._tracker_log.update_log,
                      kwargs={"entries": flights},
                      daemon=True)
      tracker_log_thread.start()

      self.logger.debug(f'Retrieved {len(flights)} flights')

      flight, route = self._flight_logic.choose_flight(flights, self._adsb_api.get_routeset)

      if flight:
        # Get plane type
        flight_capture_timestamp = datetime.now()
        plane: str = flight.get('t', "")

        # Tidy up what we pass along
        plane = plane if not (plane.upper() in BLANK_FIELDS) else ""

        # The leg the plane is on, from FlightLogic.analyze_route
        if route.get('origin') and route.get('destination'):
          origin = route['origin']
          destination = route['destination']
        else:
          origin = {'airport_iata': '', 'airport_icao': '', 'airport_lat': 0, 'airport_lon': 0}
          destination = {'airport_iata': '', 'airport_icao': '', 'airport_lat': 0, 'airport_lon': 0}

        callsign: str = flight['flight']
        if callsign.upper() in BLANK_FIELDS:
          callsign = ''

        # Get owner icao
        owner_icao = route.get('airline_code') or Overhead.tokenize_airline_code_from_callsign(callsign=callsign)

        if (route.get('airline_code')):
          airline = self._airline_lookup.lookup(route['airline_code'])
        else:
          airline = self._airline_lookup.lookup(owner_icao)

        owner_iata = airline or 'N/A'

        # Calculate distances using modified functions
        distance_origin = 0
        distance_destination = 0

        distance_origin = FlightLogic.distance_from_flight_to_location(flight, [origin['airport_lat'], origin['airport_lon']])
        distance_destination = FlightLogic.distance_from_flight_to_location(flight, [destination['airport_lat'], destination['airport_lon']])

        try:
          vertical_speed = flight['baro_rate']
        except KeyError:
          try:
            vertical_speed = flight['geom_rate']
          except KeyError:
            vertical_speed = 0
            
        origin_str: str
        destination_str: str
        if origin['airport_iata']:
          origin_str = origin['airport_iata']
        elif origin['airport_icao']:
          origin_str = origin['airport_icao'][1:]
        else:
          origin_str = ''

        if destination['airport_iata']:
          destination_str = destination['airport_iata']
        elif destination['airport_icao']:
          destination_str = destination['airport_icao'][1:]
        else:
          destination_str = ''
          
        bearing = FlightLogic.bearing((flight['lat'], flight['lon']), (self._geo_service.latitude, self._geo_service.longitude))

        try:
          data.append(
            {
              "airline": airline,
              "plane": plane,
              "origin": origin_str,
              "owner_iata": owner_iata,
              "owner_icao": owner_icao,
              "destination": destination_str,
              "vertical_speed": vertical_speed,
              "callsign": callsign,
              "registration": flight['r'],
              "distance_origin": distance_origin,
              "distance_destination": distance_destination,
              "distance": FlightLogic.distance_from_flight_to_location(flight, self._geo_service.location),
              "direction": FlightLogic.degrees_to_cardinal(bearing),
              "ground_speed": flight['gs'],
              "altitude": flight['alt_baro']
            }
          )
          
          format = "%Y-%m-%dT%H%M%S"
          date_time_formatted = flight_capture_timestamp.strftime(format)
          
          route_str = f'{origin_str} -> {destination_str}' if route.get('origin') else 'Route not available'
          
          log = {
            "Time": date_time_formatted,
            "Airline": airline,
            "Flight": callsign,
            "Route": route_str,
            "Plane": plane,
            "Altitude": f"{flight['alt_baro']} ft",
            "Ground Speed": f"{flight['gs']} kts"
          }
          
          # Serialize the log and remove bracks and quotes
          log_str = json.dumps(log).replace("{", "").replace("}", "").replace("\"", "")
          self.logger.info(log_str)
          
          with self._lock:
            self._new_data = len(data) > 0
            self._processing = False
            self._data = data
        except KeyError as e:
          self.logger.error(f'Encountered an error when processing flight {callsign}: {str(e)}')
          with self._lock:
            self._new_data = False
            self._processing = False
            self._data = []
      else:
        self.logger.info(f'No eligible flights found in the area.')
        with self._lock:
          self._new_data = False
          self._processing = False
          self._data = []

    except (ConnectionError, NewConnectionError, MaxRetryError):
      with self._lock:
        self._new_data = False
        self._processing = False
        self._data = []

  @property
  def new_data(self):
    with self._lock:
      return self._new_data

  @property
  def processing(self):
    with self._lock:
      return self._processing

  @property
  def data(self):
    with self._lock:
      self._new_data = False
      return self._data

  @property
  def data_is_empty(self):
    with self._lock:
      return len(self._data) == 0
