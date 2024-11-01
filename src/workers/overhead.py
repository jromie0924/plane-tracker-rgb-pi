from services.adsbTracker import AdsbTrackerService
from services.airlineLookup import AirlineLookupService
from services.flightLogic import FlightLogicService
from threading import Thread, Lock
from time import sleep
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from services.geo import GeoService

import threading
import math
import time
import geopy.distance as geodistance
import config

from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import MaxRetryError

RETRIES = 3
RATE_LIMIT_DELAY = 1
MAX_FLIGHT_LOOKUP = 5
EARTH_RADIUS_M = 6371000  # Earth's radius in m
BLANK_FIELDS = ["", "N/A", "NONE", "UNKNOWN"]
NW = 315  # degrees
SE = 135  # degrees

timelogs = []


def polar_to_cartesian(lat, long, alt):
  DEG2RAD = math.pi / 180
  return [
    alt * math.cos(DEG2RAD * lat) * math.sin(DEG2RAD * long),
    alt * math.sin(DEG2RAD * lat),
    alt * math.cos(DEG2RAD * lat) * math.cos(DEG2RAD * long),
  ]


# https://community.esri.com/t5/coordinate-reference-systems-blog/distance-on-a-sphere-the-haversine-formula/ba-p/902128
# Haversine formula
def distance_from_flight_to_location(flight, home=[0, 0]):
  lat1, lon1 = flight['lat'], flight['lon']
  lat2, lon2 = home[0], home[1]

  R = EARTH_RADIUS_M  # Earth's radius in meters
  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)

  delta_phi = math.radians(lat2 - lat1)
  delta_lambda = math.radians(lon2 - lon1)

  a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

  meters = R * c  # output distance in meters
  miles = round(meters * 0.000621371, 2)  # output distance in miles

  return miles


def plane_bearing(flight, home=config.LOCATION_COORDINATES_DEFAULT):
  # Convert latitude and longitude to radians
  lat1 = math.radians(home[0])
  long1 = math.radians(home[1])
  lat2 = math.radians(flight['lat'])
  long2 = math.radians(flight['lon'])

  # Calculate the bearing
  bearing = math.atan2(
    math.sin(long2 - long1) * math.cos(lat2),
    math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2 - long1)
  )

  # Convert the bearing to degrees
  bearing = math.degrees(bearing)

  # Make sure the bearing is positives
  return (bearing + 360) % 360


def degrees_to_cardinal(d):
  '''
  note: this is highly approximate...
  '''
  dirs = ["N", "NE", "E", "SE",
      "S", "SW", "W", "NW", ]
  ix = int((d + 22.5) / 45)
  return dirs[ix % 8]


class Overhead:
  def __init__(self):
    self._adsb_api = AdsbTrackerService()
    self._geo_service = GeoService()
    self._airline_lookup = AirlineLookupService()
    self._flight_logic = FlightLogicService()
    self._lock = Lock()
    self._data = []
    self._new_data = False
    self._processing = False
    self.dupe_tracker = {}

  def grab_data(self):
    while not len(self._geo_service.location):
      print('Waiting for location data...')
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

      flights = sorted(flights, key=lambda f: distance_from_flight_to_location(f, [self._geo_service.latitude, self._geo_service.longitude]))
      print(f'Retrieved {len(flights)} flights')

      # Grab a mutex lock to prevent race conditions
      with self._lock:
        # flight, route = choose_flight(flights)
        flight, route = self._flight_logic.choose_flight(flights, self._adsb_api.get_routeset)

      if flight and route and route['plausible']:
        # Get plane type
        try:
          # plane = details["aircraft"]["model"]["code"]
          plane = flight['t']
        except (KeyError, TypeError):
          plane = ""

        # Tidy up what we pass along
        plane = plane if not (plane.upper() in BLANK_FIELDS) else ""

        # origin = details['_airports'][len(details['_airports']) - 2:][0]
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

        distance_origin = distance_from_flight_to_location(flight, [origin['lat'], origin['lon']])
        distance_destination = distance_from_flight_to_location(flight, [destination['lat'], destination['lon']])

        # Get owner icao
        owner_icao = route['airline_code']

        # owner_iata = flight.airline_iata or "N/A"
        owner_iata = airline or 'N/A'

        try:
          vertical_speed = flight['baro_rate']
        except KeyError:
          try:
            vertical_speed = flight['geom_rate']
          except KeyError:
            vertical_speed = 0

        try:
          data.append(
            {
              "airline": airline,
              "plane": plane,
              "origin": origin['iata'],
              "owner_iata": owner_iata,
              "owner_icao": owner_icao,
              "destination": destination['iata'],
              "vertical_speed": vertical_speed,
              "callsign": callsign,
              "registration": flight['r'],
              "distance_origin": distance_origin,
              "distance_destination": distance_destination,
              "distance": distance_from_flight_to_location(flight, self._geo_service.location),
              "direction": degrees_to_cardinal(plane_bearing(flight)),
              "ground_speed": flight['gs'],
              "altitude": flight['alt_geom']
            }
          )
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
        print(f'No IFR flight found in the area.')
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


# Main function
if __name__ == "__main__":
  o = Overhead()
  o.grab_data()
  while not o.new_data:
    print("processing...")
    sleep(1)

  print(o.data)
