import json
from services.adsbTracker import AdsbTrackerService
from services.airlineLookup import AirlineLookupService
from services.flightLogic import FlightLogic
from threading import Thread, Lock
from time import sleep
from services.geo import GeoService

import config
import logging

from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import MaxRetryError
from datetime import datetime


EARTH_RADIUS_M = 6371000  # Earth's radius in m
BLANK_FIELDS = ["", "N/A", "NONE", "UNKNOWN"]
NW = 315  # degrees
SE = 135  # degrees

class Overhead:
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self._adsb_api = AdsbTrackerService()
    self._geo_service = GeoService()
    self._airline_lookup = AirlineLookupService()
    self._flight_logic = FlightLogic()
    self._lock = Lock()
    self._data = []
    self._new_data = False
    self._processing = False
    self.dupe_tracker = {}

  def grab_data(self):
    while not len(self._geo_service.location):
      self.logger.info('Waiting for location data...')
      sleep(1)

    Thread(target=self._grab_data).start()

  def _grab_data(self):
    # Mark data as old
    data = []

    # Grab flight details
    try:
      with self._lock:
        self._new_data = False
        self._processing = True

      flights = self._adsb_api.get_nearby_flights(self._geo_service.latitude, self._geo_service.longitude, config.RADIUS)

      if not flights or len(flights) == 0:
        with self._lock:
          self._new_data = False
          self._processing = False
          self._data = []
        sleep(0.1)
        return

      self.logger.debug(f'Retrieved {len(flights)} flights')

      # Grab a mutex lock to prevent race conditions
      with self._lock:
        flight, route = self._flight_logic.choose_flight(flights, self._adsb_api.get_routeset)

      if flight and route:
        # Get plane type
        flight_capture_timestamp = datetime.now()
        try:
          plane = flight['t']
        except (KeyError, TypeError):
          plane = ""

        # Tidy up what we pass along
        plane = plane if not (plane.upper() in BLANK_FIELDS) else ""

        airport_details = route['_airports'][len(route['_airports']) - 2:]

        if len(airport_details):
          origin = airport_details[0]
          destination = airport_details[1]
        else:
          # TODO: is this necessary?
          origin = {'iata': '', 'lat': 0, 'lon': 0, 'alt_feet': 0}
          destination = {'iata': '', 'lat': 0, 'lon': 0, 'alt_feet': 0}

        callsign: str = flight['flight']
        if callsign.upper() in BLANK_FIELDS:
          callsign = ''

        if (route['airline_code']):
          airline = self._airline_lookup.lookup(route['airline_code'])
        else:
          airline = ''

        # Calculate distances using modified functions
        distance_origin = 0
        distance_destination = 0

        distance_origin = FlightLogic.distance_from_flight_to_location(flight, [origin['lat'], origin['lon']])
        distance_destination = FlightLogic.distance_from_flight_to_location(flight, [destination['lat'], destination['lon']])

        # Get owner icao
        owner_icao = route['airline_code']
        owner_iata = airline or 'N/A'

        try:
          vertical_speed = flight['baro_rate']
        except KeyError:
          try:
            vertical_speed = flight['geom_rate']
          except KeyError:
            vertical_speed = 0
            
        origin_str: str
        destination_str: str
        if origin['iata']:
          origin_str = origin['iata']
        elif origin['icao']:
          origin_str = origin['icao'][1:]
        else:
          origin = ''
          
        if destination['iata']:
          destination_str = destination['iata']
        elif destination['icao']:
          destination_str = destination['icao'][1:]
        else:
          destination_str = ''

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
              "direction": FlightLogic.degrees_to_cardinal(FlightLogic.plane_bearing(flight)),
              "ground_speed": flight['gs'],
              "altitude": flight['alt_geom']
            }
          )
          
          format = "%Y-%m-%dT%H%M%S"
          date_time_formatted = flight_capture_timestamp.strftime(format)
          
          log = {
            "Time": date_time_formatted,
            "Airline": airline,
            "Flight": callsign,
            "Route": f'{route["_airports"][-2]["iata"]} -> {route["_airports"][-1]["iata"]}',
            "Plane": plane,
            "Altitude": f"{flight['alt_geom']} ft",
            "Ground Speed": f"{flight['gs']} kts"
          }
          
          # Serialize the log and remove bracks and quotes
          log_str = json.dumps(log).replace("{", "").replace("}", "").replace("\"", "")
          self.logger.info(log_str)
          
          with self._lock:
            self._new_data = len(data) > 0
            self._processing = False
            self._data = data
        except KeyError:
          with self._lock:
            self._new_data = False
            self._processing = False
            self._data = []
      else:
        self.logger.info(f'No IFR flight found in the area.')
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
