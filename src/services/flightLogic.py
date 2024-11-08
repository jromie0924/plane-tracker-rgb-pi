import time
import config
import logging
import math

EARTH_RADIUS_M = 6371000  # Earth's radius in m
class FlightLogic:
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self.flight_history_mapping = {}
    
  # https://community.esri.com/t5/coordinate-reference-systems-blog/distance-on-a-sphere-the-haversine-formula/ba-p/902128
  # Haversine formula
  @staticmethod
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
    note: this is highly approximate...
    '''
    dirs = ["N", "NE", "E", "SE",
        "S", "SW", "W", "NW", ]
    ix = int((d + 22.5) / 45)
    return dirs[ix % 8]
    
  # Cleanses the flight history mapping of expired entries
  # Helps prevent the mapping from taking up too much memory
  # Limiting the number of entries to 200
  def analyze_history_mapping(self):
    if len(self.flight_history_mapping) > 200:
      self.flight_history_mapping = {k: v for k, v in self.flight_history_mapping.items() if round(time.time() * 1000) - v < config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000}
    
  def validate_flight(self, flt):
    try:
      return flt['flight'] and flt['lat'] and flt['lon'] and flt['alt_baro'] and flt['hex'] and flt['t']
    except KeyError:
      return False
      
    # Get route details for a flight
  def get_details(self, flt, func):
    return func(flt['lat'], flt['lon'], flt['flight'])

  def choose_flight(self, flights, get_routeset_func: callable):
    flight, route = None, None
    
    self.logger.info(f'Cleansing duplication mapping with {len(self.flight_history_mapping)} entries.')
    self.analyze_history_mapping()

    for flt in flights:
      if not self.validate_flight(flt):
        continue

      if flt['alt_baro'] <= config.MAX_ALTITUDE and flt['alt_baro'] >= config.MIN_ALTITUDE:
        flt_key = flt['hex'].strip().upper()
        
        if flt_key in self.flight_history_mapping:
          timestamp = round(time.time() * 1000)

          # If the flight is older than the TTL, update the timestamp
          if timestamp - self.flight_history_mapping[flt_key] > config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000:
            flight_num = flt['flight']
            self.logger.info(f'Flight {flight_num} has expired from the dupe tracker.')
            flight = flt
            route = self.get_details(flt, func=get_routeset_func)
        else:
          flight = flt
          route = self.get_details(flt, func=get_routeset_func)
        try:
          if route and route['plausible']:
            self.flight_history_mapping[flt_key] = round(time.time() * 1000)
            break
          else:
            route = None
        except KeyError:
          route = None
          continue
    return (flight, route) if flight and route else (None, None)