import time
import config

class FlightLogicService:
  def __init__(self):
    self.dupe_tracker = {}
    
  def analyze_dupe_tracker(self):
    if len(self.dupe_tracker) > 1000:
      self.dupe_tracker = {k: v for k, v in self.dupe_tracker.items() if round(time.time() * 1000) - v < config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000}
    
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
    
    print(f'Cleansing duplication mapping with {len(self.dupe_tracker)} entries.')
    self.analyze_dupe_tracker()

    for flt in flights:
      if not self.validate_flight(flt):
        continue

      if flt['alt_baro'] <= config.MAX_ALTITUDE and flt['alt_baro'] >= config.MIN_ALTITUDE:
        flt_key = flt['hex'].strip().upper()
        
        if flt_key in self.dupe_tracker:
          timestamp = round(time.time() * 1000)

          # If the flight is older than the TTL, update the timestamp
          if timestamp - self.dupe_tracker[flt_key] > config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000:
            flight_num = flt['flight']
            print(f'Flight {flight_num} has expired from the dupe tracker.')
            flight = flt
            route = self.get_details(flt, func=get_routeset_func)
        else:
          flight = flt
          route = self.get_details(flt, func=get_routeset_func)
        try:
          if route and route['plausible']:
            self.dupe_tracker[flt_key] = round(time.time() * 1000)
            break
          else:
            route = None
        except KeyError:
          route = None
          continue
    return (flight, route) if flight and route else (None, None)