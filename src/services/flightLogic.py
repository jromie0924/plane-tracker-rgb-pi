import config
import logging
import math

from services.geo import GeoService
from utils.timeUtils import TimeUtils

EARTH_RADIUS_M = 6371000  # Earth's radius in m
EARTH_RADIUS_NM = 3440.065  # Earth's radius in nautical miles

# Route analysis (see analyze_route). Distances are in nautical miles, altitudes in feet.
# These are starting points, to be tuned against real traffic.
ROUTE_MIN_LEG_NM = 1  # shorter legs (e.g. the same airport twice in a row) are skipped
ROUTE_CROSS_TRACK_MIN_NM = 40  # how far off a leg's path the plane can be...
ROUTE_CROSS_TRACK_FRACTION = 0.1  # ...or this fraction of the leg's length, whichever is larger
ROUTE_ENDPOINT_SLACK_NM = 30  # how far before the origin or past the destination the plane can be (vectors, downwinds)
ROUTE_TERMINAL_AREA_NM = 40  # within this of an airport, the plane is departing or arriving
ROUTE_ARRIVAL_FT_PER_NM = 350  # max height above the destination per nm out (~3:1 descent)
ROUTE_DEPARTURE_FT_PER_NM = 1000  # max height above the origin per nm out
ROUTE_ALTITUDE_BUFFER_FT = 2000  # added to both, also covers alt_baro being pressure altitude
ROUTE_VERTICAL_RATE_DEADBAND_FPM = 500  # rates within this are treated as level
ROUTE_SCORE_WEIGHTS = {'geometry': 1, 'heading': 2, 'vertical': 2}
ROUTE_MIN_SCORE = 0.5  # the best leg must score at least this to be plausible
ROUTE_TIE_MARGIN = 0.1  # if the top two legs are closer than this, it's too close to call

ARRIVAL, DEPARTURE, EN_ROUTE = 'arrival', 'departure', 'en route'

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
  
  # Bearing in degrees (0-360) from a to b, both (lat, lon).
  @staticmethod
  def bearing(a: tuple, b: tuple):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    bearing = math.atan2(
      math.sin(lon2 - lon1) * math.cos(lat2),
      math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1)
    )
    return (math.degrees(bearing) + 360) % 360
  
  
  @staticmethod
  def degrees_to_cardinal(deg: float):
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
    
    idx = int((deg + 11.25) / 22.5)
    return dirs[idx % 16]
    
  # Cleanses the flight history mapping of expired entries
  # Helps prevent the mapping from taking up too much memory
  def _cleanse_history_mapping(self):
    start = len(self.flight_history_mapping)
    self.flight_history_mapping = {k: v for k, v in self.flight_history_mapping.items()
                                   if round(TimeUtils.current_time_milli()) - v < config.DUPLICATION_AVOIDANCE_TTL * 60 * 1000}
    end = len(self.flight_history_mapping)
    diff = start - end
    self.logger.debug(f'Cleansed {diff} {"entry" if diff == 1 else "entries"} from the history mapping.')
    self.logger.debug(f'History mapping now contains {len(self.flight_history_mapping)} entries.')
    
  def validate_flight(self, flt):
    try:
      return flt['flight'] and flt['lat'] and flt['lon'] and flt['alt_baro'] and flt['hex'] and flt['t']
    except KeyError:
      return False

  # Picks the nearest flight with a plausible route, returning (flight, route) where route
  # is from analyze_route. Falls back to (first flight, {}) if none has one.
  def choose_flight(self, flights, get_routeset_func: callable) -> tuple[dict, dict]:
    flights = [f for f in flights if self.validate_flight(f)]
    self._cleanse_history_mapping()

    candidates = sorted(flights, key=lambda f: self.distance_from_flight_to_location(f, self._geo_service.location))
    candidates = [f for f in candidates if config.MIN_ALTITUDE <= f['alt_baro'] <= config.MAX_ALTITUDE]

    routes = get_routeset_func(candidates) if candidates else None
    if routes:
      for flight in candidates:
        stops = routes.get(flight['flight'].strip())
        if not stops:
          continue

        route = self.analyze_route(flight, stops)
        if route is None:
          continue

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

  def analyze_route(self, flight, stops):
    '''
    Works out which leg of a route the plane is on, from where it is and what it's doing.
    stops are the route's airports in order, as returned by get_routeset (e.g. KSFO, KORD, CYYZ).

    Each consecutive pair of stops is a leg (KSFO->KORD, KORD->CYYZ). A leg is ruled out if
    the plane is too far off its path, too far before its origin or past its destination, or
    too high to have just departed or to be about to land. The rest are scored 0 to 1 on:
      - geometry: how close the plane is to the leg's path
      - heading: whether the plane's track points at the leg's destination. Only en route,
        since near airports planes are vectored and fly downwinds.
      - vertical: arriving planes should be descending, departing planes climbing

    Returns {'origin': stop, 'destination': stop, 'leg': index, 'score': score} for the best
    leg, or None if no leg is plausible or the best two are too close to call.
    '''
    plane = (flight['lat'], flight['lon'])

    scored = []
    for leg, (origin, destination) in enumerate(zip(stops, stops[1:])):
      score = self._score_leg(flight, plane, origin, destination)
      self.logger.debug(f'{flight["flight"].strip()} leg {origin["airport_icao"]}->{destination["airport_icao"]}: '
                        f'{"ruled out" if score is None else f"{score:.2f}"}')
      if score is not None:
        scored.append((score, leg, origin, destination))

    if not scored:
      return None

    scored.sort(key=lambda s: s[0], reverse=True)
    score, leg, origin, destination = scored[0]

    if score < ROUTE_MIN_SCORE:
      return None
    if len(scored) > 1 and score - scored[1][0] < ROUTE_TIE_MARGIN:
      return None

    return {'origin': origin, 'destination': destination, 'leg': leg, 'score': score}

  # Scores how well one leg fits the plane, from 0 to 1, or None if it's ruled out.
  @staticmethod
  def _score_leg(flight, plane_coords, origin, destination):
    a: tuple = (origin['airport_lat'], origin['airport_lon'])
    b: tuple = (destination['airport_lat'], destination['airport_lon'])

    leg_nm = FlightLogic._distance_nm(a, b)
    if leg_nm < ROUTE_MIN_LEG_NM:
      return None

    cross_nm, along_nm = FlightLogic._cross_along_track(a, b, plane_coords)
    cross_limit_nm = max(ROUTE_CROSS_TRACK_MIN_NM, ROUTE_CROSS_TRACK_FRACTION * leg_nm)
    if abs(cross_nm) > cross_limit_nm:
      return None
    if along_nm < -ROUTE_ENDPOINT_SLACK_NM or along_nm > leg_nm + ROUTE_ENDPOINT_SLACK_NM:
      return None

    from_origin_nm = FlightLogic._distance_nm(a, plane_coords)
    to_destination_nm = FlightLogic._distance_nm(plane_coords, b)

    if to_destination_nm <= ROUTE_TERMINAL_AREA_NM and to_destination_nm <= from_origin_nm:
      phase = ARRIVAL
      ceiling = (destination.get('airport_alt_feet') or 0) + ROUTE_ARRIVAL_FT_PER_NM * to_destination_nm
    elif from_origin_nm <= ROUTE_TERMINAL_AREA_NM:
      phase = DEPARTURE
      ceiling = (origin.get('airport_alt_feet') or 0) + ROUTE_DEPARTURE_FT_PER_NM * from_origin_nm
    else:
      phase = EN_ROUTE
      ceiling = None

    if ceiling is not None and flight['alt_baro'] > ceiling + ROUTE_ALTITUDE_BUFFER_FT:
      return None

    scores = {
      'geometry': 1 - abs(cross_nm) / cross_limit_nm,
      'heading': FlightLogic._heading_score(flight, plane_coords, b, phase),
      'vertical': FlightLogic._vertical_score(flight, phase),
    }

    # Components that couldn't be scored (no data, or not meaningful here) are left out
    # rather than counted as 0, so missing data doesn't penalize a leg.
    weights = {k: ROUTE_SCORE_WEIGHTS[k] for k, v in scores.items() if v is not None}
    return sum(scores[k] * w for k, w in weights.items()) / sum(weights.values())

  # 1 when the plane's track points straight at the destination, falling to 0 at 90º off.
  # On a great circle the track always points at the destination from wherever the plane
  # is, so this holds for long, curved-looking routes too.
  @staticmethod
  def _heading_score(flight, plane, destination, phase):
    track = flight.get('track')
    if track is None or phase != EN_ROUTE:
      return None
    off_by = abs((track - FlightLogic.bearing(plane, destination) + 180) % 360 - 180)
    return max(0.0, math.cos(math.radians(off_by)))

  # 1 when climbing out of the origin or descending into the destination, 0.5 when level,
  # 0 when going the wrong way. Not scored en route, where any of these is normal.
  @staticmethod
  def _vertical_score(flight, phase):
    rate = flight.get('baro_rate', flight.get('geom_rate'))
    if rate is None or phase == EN_ROUTE:
      return None
    if abs(rate) < ROUTE_VERTICAL_RATE_DEADBAND_FPM:
      return 0.5
    expected = 1 if phase == DEPARTURE else -1
    return 1.0 if rate * expected > 0 else 0.0

  # Great-circle distance in nautical miles between two (lat, lon) points.
  @staticmethod
  def _distance_nm(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_NM * math.asin(math.sqrt(min(1.0, h)))

  # Where point p sits relative to the great circle from a to b, as (cross, along) in nm.
  # cross is how far p is off the path (the sign says which side). along is how far p is
  # from a, measured along the path, negative if p is behind a.
  # https://www.movable-type.co.uk/scripts/latlong.html#cross-track
  @staticmethod
  def _cross_along_track(a: tuple, b: tuple, plane_coords: tuple):
    a_to_p = FlightLogic._distance_nm(a, plane_coords) / EARTH_RADIUS_NM  # angular distance
    angle = math.radians(FlightLogic.bearing(a, plane_coords) - FlightLogic.bearing(a, b))

    cross = math.asin(math.sin(a_to_p) * math.sin(angle))
    along = math.acos(max(-1.0, min(1.0, math.cos(a_to_p) / math.cos(cross))))
    if math.cos(angle) < 0:
      along = -along

    return cross * EARTH_RADIUS_NM, along * EARTH_RADIUS_NM
