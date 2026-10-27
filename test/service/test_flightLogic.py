import math
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from services.flightLogic import FlightLogic, EARTH_RADIUS_NM


VALID_FLIGHT = {
  'hex': 'abc123',
  'flight': 'UAL123',
  'lat': 41.8781,
  'lon': -87.6298,
  'alt_baro': 15000,
  't': 'A320',
}


# FlightLogic is a singleton, so reset it to stop flight history leaking between tests.
@pytest.fixture(autouse=True)
def reset_flight_logic_singleton():
  FlightLogic._instance = None
  yield
  FlightLogic._instance = None


@pytest.fixture
def mock_config():
  with patch('services.flightLogic.config') as mock_config:
    mock_config.APP_NAME = 'test_app'
    mock_config.DUPLICATION_AVOIDANCE_TTL = 5
    mock_config.MAX_ALTITUDE = 50000
    mock_config.MIN_ALTITUDE = 1000
    mock_config.LOCATION_COORDINATES_DEFAULT = [41.8781, -87.6298]
    yield mock_config


@pytest.fixture
def mock_geo_service():
  with patch('services.flightLogic.GeoService') as mock_geo_cls:
    mock_geo = MagicMock()
    mock_geo.location = [41.8781, -87.6298]
    mock_geo_cls.return_value = mock_geo
    yield mock_geo


@pytest.fixture
def mock_time_utils():
  with patch('services.flightLogic.TimeUtils') as mock_time:
    mock_time.current_time_milli.return_value = 1000000
    yield mock_time


def make_flight(**overrides):
  flight = VALID_FLIGHT.copy()
  flight.update(overrides)
  return flight


def make_stop(icao, iata, lat, lon, alt_feet):
  return {'airport_icao': icao, 'airport_iata': iata, 'airport_lat': lat, 'airport_lon': lon, 'airport_alt_feet': alt_feet}


SFO = make_stop('KSFO', 'SFO', 37.618999, -122.375, 13)
ORD = make_stop('KORD', 'ORD', 41.9786, -87.9048, 680)
YYZ = make_stop('CYYZ', 'YYZ', 43.6772, -79.6306, 569)
LAX = make_stop('KLAX', 'LAX', 33.942501, -118.407997, 125)
JFK = make_stop('KJFK', 'JFK', 40.639801, -73.7789, 13)
DEN = make_stop('KDEN', 'DEN', 39.861698, -104.672997, 5434)
FRA = make_stop('EDDF', 'FRA', 50.033333, 8.570556, 364)


def position(stop):
  return (stop['airport_lat'], stop['airport_lon'])


# The point a given distance (nm) from a, along the great circle from a to b.
def point_along(a, b, nm):
  a, b = position(a), position(b)
  lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
  d = FlightLogic._distance_nm(a, b) / EARTH_RADIUS_NM
  f = nm / (d * EARTH_RADIUS_NM)
  wa = math.sin((1 - f) * d) / math.sin(d)
  wb = math.sin(f * d) / math.sin(d)
  x = wa * math.cos(lat1) * math.cos(lon1) + wb * math.cos(lat2) * math.cos(lon2)
  y = wa * math.cos(lat1) * math.sin(lon1) + wb * math.cos(lat2) * math.sin(lon2)
  z = wa * math.sin(lat1) + wb * math.sin(lat2)
  return math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))


def leg_nm(a, b):
  return FlightLogic._distance_nm(position(a), position(b))


# A flight at a point, optionally pointed at a stop (track set to the bearing to it).
def flight_at(point, toward=None, **overrides):
  flight = make_flight(lat=point[0], lon=point[1])
  if toward is not None:
    flight['track'] = FlightLogic.bearing(point, position(toward))
  flight.update(overrides)
  return flight


def routes_for(flight, stops):
  return lambda flights: {flight['flight']: stops}


# --- choose_flight: fallback behavior (the primary change in this branch) ---

def test_choose_flight_returns_first_flight_with_empty_route_when_no_routes(mock_config, mock_geo_service, mock_time_utils):
  """When get_routeset_func returns empty, choose_flight should return the first flight with an empty dict route."""
  logic = FlightLogic()
  flight1 = make_flight(hex='aaa', flight='AAL100')
  flight2 = make_flight(hex='bbb', flight='DAL200')

  result_flight, result_route = logic.choose_flight([flight1, flight2], get_routeset_func=lambda flights: [])

  assert result_flight == flight1
  assert result_route == {}


def test_choose_flight_returns_none_empty_dict_when_no_flights(mock_config, mock_geo_service, mock_time_utils):
  """When flights list is empty, choose_flight should return (None, {})."""
  logic = FlightLogic()

  result_flight, result_route = logic.choose_flight([], get_routeset_func=lambda flights: [])

  assert result_flight is None
  assert result_route == {}


def test_choose_flight_fallback_route_is_dict_not_none(mock_config, mock_geo_service, mock_time_utils):
  """Fallback route should always be a dict, never None."""
  logic = FlightLogic()
  flight = make_flight()

  _, result_route = logic.choose_flight([flight], get_routeset_func=lambda flights: [])

  assert result_route is not None
  assert isinstance(result_route, dict)


def test_choose_flight_no_flights_route_is_dict_not_none(mock_config, mock_geo_service, mock_time_utils):
  """Even when no flights, second return value should be {} not None."""
  logic = FlightLogic()

  _, result_route = logic.choose_flight([], get_routeset_func=lambda flights: [])

  assert result_route is not None
  assert isinstance(result_route, dict)


# --- choose_flight: normal route-based selection still works ---

def test_choose_flight_returns_flight_with_route_when_routes_available(mock_config, mock_geo_service, mock_time_utils):
  """When the flight's route is plausible, the flight and its analyzed route should be returned."""
  logic = FlightLogic()
  flight = make_flight()  # just southeast of ORD, at 15,000 ft

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=routes_for(flight, [ORD, JFK]))

  assert result_flight == flight
  assert result_route['origin'] == ORD
  assert result_route['destination'] == JFK


def test_choose_flight_skips_implausible_routes(mock_config, mock_geo_service, mock_time_utils):
  """Implausible routes should be skipped; fallback to first flight if none are plausible."""
  logic = FlightLogic()
  flight = make_flight()

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=routes_for(flight, [SFO, DEN]))

  assert result_flight == flight
  assert result_route == {}


def test_choose_flight_skips_routes_with_a_single_stop(mock_config, mock_geo_service, mock_time_utils):
  """A route with only one airport has no legs, so it isn't plausible."""
  logic = FlightLogic()
  flight = make_flight()

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=routes_for(flight, [ORD]))

  assert result_flight == flight
  assert result_route == {}


def test_choose_flight_skips_flights_without_a_route(mock_config, mock_geo_service, mock_time_utils):
  """A flight with no route in the database is passed over for one that has a plausible route."""
  logic = FlightLogic()
  no_route = make_flight(hex='aaa', flight='AAL100')
  with_route = make_flight(hex='bbb', flight='UAL123')

  result_flight, result_route = logic.choose_flight([no_route, with_route],
                                                    get_routeset_func=routes_for(with_route, [ORD, JFK]))

  assert result_flight == with_route
  assert result_route['destination'] == JFK


def test_choose_flight_looks_up_routes_by_stripped_callsign(mock_config, mock_geo_service, mock_time_utils):
  """readsb pads callsigns with spaces, while the route database doesn't."""
  logic = FlightLogic()
  flight = make_flight(flight='UAL123  ')

  _, result_route = logic.choose_flight([flight], get_routeset_func=lambda flights: {'UAL123': [ORD, JFK]})

  assert result_route['destination'] == JFK


def test_choose_flight_filters_invalid_flights(mock_config, mock_geo_service, mock_time_utils):
  """Flights missing required fields should be filtered before selection."""
  logic = FlightLogic()
  invalid_flight = {'hex': 'xyz'}  # missing lat, lon, flight, alt_baro, t
  valid_flight = make_flight()

  result_flight, result_route = logic.choose_flight(
    [invalid_flight, valid_flight],
    get_routeset_func=lambda flights: []
  )

  assert result_flight == valid_flight


def test_choose_flight_all_invalid_flights_returns_none(mock_config, mock_geo_service, mock_time_utils):
  """If all flights are invalid, should return (None, {})."""
  logic = FlightLogic()
  invalid_flight = {'hex': 'xyz'}

  result_flight, result_route = logic.choose_flight(
    [invalid_flight],
    get_routeset_func=lambda flights: []
  )

  assert result_flight is None
  assert result_route == {}


# --- degrees_to_cardinal ---

CARDINALS = ["N", "NNE", "NE", "ENE",
             "E", "ESE", "SE", "SSE",
             "S", "SSW", "SW", "WSW",
             "W", "WNW", "NW", "NNW"]


@pytest.mark.parametrize("index,expected", list(enumerate(CARDINALS)))
def test_degrees_to_cardinal_sector_centers(index, expected):
  """Each cardinal's center bearing (a multiple of 22.5) maps to that cardinal."""
  assert FlightLogic.degrees_to_cardinal(index * 22.5) == expected


@pytest.mark.parametrize("index", range(16))
def test_degrees_to_cardinal_sector_boundaries(index):
  """A sector's lower edge belongs to it; anything just below belongs to the previous sector."""
  lower_edge = (index * 22.5 - 11.25) % 360
  assert FlightLogic.degrees_to_cardinal(lower_edge) == CARDINALS[index]
  assert FlightLogic.degrees_to_cardinal(lower_edge - 0.01) == CARDINALS[index - 1]


@pytest.mark.parametrize("degrees", [348.75, 350, 355, 359.99, 360])
def test_degrees_to_cardinal_wraps_to_north_near_360(degrees):
  """Bearings in the top half of N's sector overflow to index 16 and must wrap back to N."""
  assert FlightLogic.degrees_to_cardinal(degrees) == "N"


@pytest.mark.parametrize("degrees,expected", [
  (12, "NNE"),
  (280, "W"),
  (290, "WNW"),
  (315, "NW"),
  (337.5, "NNW"),
])
def test_degrees_to_cardinal_arbitrary_bearings(degrees, expected):
  assert FlightLogic.degrees_to_cardinal(degrees) == expected


# --- geometry helpers ---

def test_distance_nm():
  """ORD to JFK is about 640 nm."""
  assert FlightLogic._distance_nm(position(ORD), position(JFK)) == pytest.approx(640, abs=5)


def test_bearing():
  """Due east along the equator is 90º, due north is 0º."""
  assert FlightLogic.bearing((0, 0), (0, 10)) == pytest.approx(90)
  assert FlightLogic.bearing((0, 0), (10, 0)) == pytest.approx(0)


def test_cross_along_track_for_a_point_on_the_path():
  plane = point_along(LAX, JFK, 1000)

  cross, along = FlightLogic._cross_along_track(position(LAX), position(JFK), plane)

  assert cross == pytest.approx(0, abs=0.1)
  assert along == pytest.approx(1000, abs=0.1)


def test_cross_along_track_is_negative_behind_the_origin():
  """A point behind the origin (west of ORD, on an eastbound leg) has a negative along-track distance."""
  plane = point_along(ORD, SFO, 20)

  _, along = FlightLogic._cross_along_track(position(ORD), position(YYZ), plane)

  assert along < 0


# --- analyze_route ---

def test_analyze_route_arriving_at_a_local_airport(mock_config, mock_geo_service):
  """Descending, 30 nm out from ORD on the SFO->ORD path."""
  logic = FlightLogic()
  flight = flight_at(point_along(SFO, ORD, leg_nm(SFO, ORD) - 30), toward=ORD, alt_baro=9000, baro_rate=-1200)

  route = logic.analyze_route(flight, [SFO, ORD])

  assert route['origin'] == SFO
  assert route['destination'] == ORD


def test_analyze_route_overflight(mock_config, mock_geo_service):
  """Level at cruise, partway along LAX->JFK and heading for JFK."""
  logic = FlightLogic()
  flight = flight_at(point_along(LAX, JFK, 1300), toward=JFK, alt_baro=37000, baro_rate=0)

  route = logic.analyze_route(flight, [LAX, JFK])

  assert route['origin'] == LAX
  assert route['destination'] == JFK


def test_analyze_route_overflight_on_a_route_that_curves_on_a_flat_map(mock_config, mock_geo_service):
  """FRA->DEN goes up over Canada, north of both airports, and is still on its path."""
  logic = FlightLogic()
  plane = point_along(FRA, DEN, leg_nm(FRA, DEN) * 0.6)
  flight = flight_at(plane, toward=DEN, alt_baro=37000, baro_rate=0)

  route = logic.analyze_route(flight, [FRA, DEN])

  assert plane[0] > FRA['airport_lat'] and plane[0] > DEN['airport_lat']
  assert route['destination'] == DEN


def test_analyze_route_rejects_overflight_heading_the_wrong_way(mock_config, mock_geo_service):
  """On the LAX->JFK path, but heading for LAX."""
  logic = FlightLogic()
  flight = flight_at(point_along(LAX, JFK, 1300), toward=LAX, alt_baro=37000, baro_rate=0)

  assert logic.analyze_route(flight, [LAX, JFK]) is None


def test_analyze_route_picks_arriving_leg_of_multi_stop_route(mock_config, mock_geo_service):
  """Descending into ORD on SFO->ORD->YYZ: on the SFO->ORD leg."""
  logic = FlightLogic()
  flight = flight_at(point_along(SFO, ORD, leg_nm(SFO, ORD) - 30), toward=ORD, alt_baro=9000, baro_rate=-1200)

  route = logic.analyze_route(flight, [SFO, ORD, YYZ])

  assert route['leg'] == 0
  assert route['origin'] == SFO
  assert route['destination'] == ORD


def test_analyze_route_picks_departing_leg_of_multi_stop_route(mock_config, mock_geo_service):
  """Climbing out of ORD toward YYZ on SFO->ORD->YYZ: on the ORD->YYZ leg."""
  logic = FlightLogic()
  flight = flight_at(point_along(ORD, YYZ, 30), toward=YYZ, alt_baro=9000, baro_rate=2000)

  route = logic.analyze_route(flight, [SFO, ORD, YYZ])

  assert route['leg'] == 1
  assert route['origin'] == ORD
  assert route['destination'] == YYZ


def test_analyze_route_is_none_when_legs_are_too_close_to_call(mock_config, mock_geo_service):
  """Level just west of ORD on SFO->ORD->YYZ could be arriving at ORD or about to turn for YYZ."""
  logic = FlightLogic()
  flight = flight_at(point_along(SFO, ORD, leg_nm(SFO, ORD) - 15), alt_baro=5000, baro_rate=0)

  assert logic.analyze_route(flight, [SFO, ORD, YYZ]) is None


def test_analyze_route_rejects_route_the_plane_is_nowhere_near(mock_config, mock_geo_service):
  """SFO->DEN for a plane over Chicago."""
  logic = FlightLogic()
  flight = flight_at(position(ORD), alt_baro=9000, baro_rate=-1200, track=90)

  assert logic.analyze_route(flight, [SFO, DEN]) is None


def test_analyze_route_rejects_arrival_when_too_high_to_land(mock_config, mock_geo_service):
  """At FL370 20 nm out, the plane can't be landing at ORD."""
  logic = FlightLogic()
  flight = flight_at(point_along(SFO, ORD, leg_nm(SFO, ORD) - 20), toward=ORD, alt_baro=37000, baro_rate=0)

  assert logic.analyze_route(flight, [SFO, ORD]) is None


def test_analyze_route_allows_for_destination_elevation(mock_config, mock_geo_service):
  """DEN is at 5,434 ft, so arrivals there are higher above sea level for the same distance out."""
  logic = FlightLogic()
  flight = flight_at(point_along(ORD, DEN, leg_nm(ORD, DEN) - 30), toward=DEN, alt_baro=16000, baro_rate=-1500)

  route = logic.analyze_route(flight, [ORD, DEN])

  assert route['destination'] == DEN


def test_analyze_route_skips_zero_length_legs(mock_config, mock_geo_service):
  """A route that repeats an airport back to back has a zero-length leg, which is skipped."""
  logic = FlightLogic()
  flight = flight_at(point_along(SFO, ORD, leg_nm(SFO, ORD) - 30), toward=ORD, alt_baro=9000, baro_rate=-1200)

  assert logic.analyze_route(flight, [ORD, ORD]) is None
  assert logic.analyze_route(flight, [SFO, ORD, ORD])['destination'] == ORD


def test_analyze_route_without_track_or_vertical_rate(mock_config, mock_geo_service):
  """With no track or vertical rate, a plane on a leg's path is still plausible on geometry alone."""
  logic = FlightLogic()
  flight = flight_at(point_along(LAX, JFK, 1300), alt_baro=37000)

  route = logic.analyze_route(flight, [LAX, JFK])

  assert route['destination'] == JFK
