import config
import logging
import math

from services.geo import GeoService
from utils.timeUtils import TimeUtils

EARTH_RADIUS_M = 6371000  # Earth's radius in m
class FlightLogic:
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self.flight_history_mapping = {}
    self._geo_service = GeoService()
    
  # https://community.esri.com/t5/coordinate-reference-systems-blog/distance-on-a-sphere-the-haversine-formula/ba-p/902128
  # Haversine formula
  @staticmethod
  def distance_from_flight_to_location(flight, home=[0, 0]):
    if [0,0] == home:
      return 0
    
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
  
  @staticmethod
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
  
  
  @staticmethod
  def degrees_to_cardinal(d):
    '''
    The math:
    
    We have 16 cardinals defined below. Dividing 360º by 16 gives 22.5º,
    so the compass is split into 16 sectors ("pizza slices"), each 22.5º wide.

    Each cardinal is centered on its sector, so N covers 348.75º-11.25º
    (i.e. ±11.25º, half a sector's width, around 0º).

    To find the sector for a given degree:
      1. Add 11.25º to shift the circle by half a sector's width, so each
         sector starts on a multiple of 22.5º.
      2. Divide by the sector width (22.5º) to get how many sectors in we are.
      3. Drop the decimal to get the index into the array.

    Example: 12º
      12 + 11.25 = 23.25
      23.25 / 22.5 = 1.03 => 1
      Index 1 is the second cardinal in the array: NNE.
    '''
    dirs = ["N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW"]
    
    ix = int((d + 11.25) / 22.5)
    return dirs[ix % 16]
    
  # Cleanses the flight history mapping of expired entries
  # Helps prevent the mapping from taking up too much memory
  def _cleanse_history_mapping(self):
    start = len(self.flight_history_mapping)
    self.flight_history_mapping = {k: v for k, v in self.flight_history_mapping.items() if round(TimeUtils.current_time_milli()) - v < config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000}
    end = len(self.flight_history_mapping)
    diff = start - end
    self.logger.debug(f'Cleansed {diff} {"entry" if diff == 1 else "entries"} from the history mapping.')
    self.logger.debug(f'History mapping now contains {len(self.flight_history_mapping)} entries.')
    
  def validate_flight(self, flt):
    try:
      return flt['flight'] and flt['lat'] and flt['lon'] and flt['alt_baro'] and flt['hex'] and flt['t']
    except KeyError:
      return False

  def choose_flight(self, flights, get_routeset_func: callable):
    flight, route = None, None
    
    flights = [f for f in flights if self.validate_flight(f)]
    self._cleanse_history_mapping()
    
    flights_with_routes = get_routeset_func(flights)
    if flights_with_routes:
      flights_with_routes = sorted(flights_with_routes, key=lambda f: self.distance_from_flight_to_location(f['flight'], self._geo_service.location))
      flights_with_routes = [f for f in flights_with_routes if f['flight']['alt_baro'] <= config.MAX_ALTITUDE and f['flight']['alt_baro'] >= config.MIN_ALTITUDE]
      for item in flights_with_routes:
        flight, route = None, None
        if item['route']['plausible'] and len(item['route']['_airports']) == 2:
          flight = item['flight']
          route = item['route']
          timestamp = TimeUtils.current_time_milli()
          if flight['hex'] in self.flight_history_mapping:
            if timestamp - self.flight_history_mapping[flight['hex']] >= config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000:
              self.flight_history_mapping[flight['hex']] = timestamp
              return flight, route
            else:
              continue
          self.flight_history_mapping[flight['hex']] = timestamp
          return flight, route

    if flights:
      return flights[0], {}
    return None, {}
