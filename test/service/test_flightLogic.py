import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from services.flightLogic import FlightLogic


VALID_FLIGHT = {
  'hex': 'abc123',
  'flight': 'UAL123',
  'lat': 41.8781,
  'lon': -87.6298,
  'alt_baro': 15000,
  't': 'A320',
}


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


def make_route_item(flight, plausible=True, airports=None):
  if airports is None:
    airports = [
      {'iata': 'ORD', 'icao': 'KORD', 'lat': 41.9, 'lon': -87.9, 'alt_feet': 668},
      {'iata': 'JFK', 'icao': 'KJFK', 'lat': 40.6, 'lon': -73.8, 'alt_feet': 13},
    ]
  return {
    'flight': flight,
    'route': {
      'plausible': plausible,
      '_airports': airports,
      'airline_code': 'UAL',
    }
  }


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
  """When routes are available, the flight+route pair should be returned (not the fallback)."""
  logic = FlightLogic()
  flight = make_flight()
  route_item = make_route_item(flight)

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=lambda flights: [route_item])

  assert result_flight == flight
  assert result_route.get('airline_code') == 'UAL'
  assert len(result_route['_airports']) == 2


def test_choose_flight_skips_implausible_routes(mock_config, mock_geo_service, mock_time_utils):
  """Implausible routes should be skipped; fallback to first flight if none are plausible."""
  logic = FlightLogic()
  flight = make_flight()
  implausible_route_item = make_route_item(flight, plausible=False)

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=lambda flights: [implausible_route_item])

  # No plausible route found → fallback to first flight with empty route
  assert result_flight == flight
  assert result_route == {}


def test_choose_flight_skips_routes_with_wrong_airport_count(mock_config, mock_geo_service, mock_time_utils):
  """Routes with airport count != 2 should be skipped."""
  logic = FlightLogic()
  flight = make_flight()
  route_item = make_route_item(flight, airports=[
    {'iata': 'ORD', 'icao': 'KORD', 'lat': 41.9, 'lon': -87.9, 'alt_feet': 668}
  ])  # only 1 airport

  result_flight, result_route = logic.choose_flight([flight], get_routeset_func=lambda flights: [route_item])

  assert result_flight == flight
  assert result_route == {}


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
