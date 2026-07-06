import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from workers.overhead import Overhead


def make_flight(**overrides):
  flight = {
    'flight': 'QTR8170',
    't': 'B77W',
    'r': 'A7-BEA',
    'gs': 480,
    'alt_geom': 38000,
    'baro_rate': 0,
    'lat': 41.9,
    'lon': -87.9,
    'track': 90,
  }
  flight.update(overrides)
  return flight


@pytest.fixture
def overhead():
  """
  Build an Overhead with its heavy collaborators mocked out, but keep the
  real AirlineLookupService so the ICAO -> airline name resolution is
  genuinely exercised.
  """
  with patch('workers.overhead.AdsbTrackerService') as mock_adsb_cls, \
       patch('workers.overhead.GeoService') as mock_geo_cls, \
       patch('workers.overhead.FlightLogic') as mock_flight_logic_cls, \
       patch('workers.overhead.TrackerLog') as mock_tracker_log_cls:

    mock_geo = mock_geo_cls.return_value
    mock_geo.location = [41.8781, -87.6298]
    mock_geo.latitude = 41.8781
    mock_geo.longitude = -87.6298

    # Static methods used while assembling the data dict — values are
    # irrelevant to this test, so let them return simple stand-ins.
    mock_flight_logic_cls.distance_from_flight_to_location.return_value = 0
    mock_flight_logic_cls.degrees_to_cardinal.return_value = 'N'
    mock_flight_logic_cls.plane_bearing.return_value = 0

    yield Overhead()


def test_airline_name_falls_back_to_callsign_icao_when_route_unavailable(overhead):
  """
  When no route (and thus no airline_code) is available, the airline name
  should still be resolved from the ICAO tokenized out of the callsign.
  QTR8170 -> QTR -> "Qatar Airways".
  """
  flight = make_flight(flight='QTR8170')
  # Route unavailable: empty dict, matching FlightLogic's fallback.
  route = {}

  overhead._adsb_api.get_nearby_flights.return_value = [flight]
  overhead._flight_logic.choose_flight.return_value = (flight, route)

  overhead._grab_data()

  assert overhead.new_data is True
  data = overhead.data
  assert len(data) == 1
  assert data[0]['airline'] == 'Qatar Airways'
  assert data[0]['owner_icao'] == 'QTR'
  assert data[0]['owner_iata'] == 'Qatar Airways'


def test_airline_name_uses_route_airline_code_when_available(overhead):
  """
  Sanity check the non-fallback path still works: when the route provides an
  airline_code, it is used directly for the lookup.
  """
  flight = make_flight(flight='UAL123')
  route = {'airline_code': 'UAL'}

  overhead._adsb_api.get_nearby_flights.return_value = [flight]
  overhead._flight_logic.choose_flight.return_value = (flight, route)

  overhead._grab_data()

  data = overhead.data
  assert len(data) == 1
  assert data[0]['airline'] == 'United Airlines'
  assert data[0]['owner_icao'] == 'UAL'
