import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from workers.overhead import Overhead


def make_flight(**overrides):
  flight = {
    'flight': 'UAL1234',
    't': 'B77W',
    'r': 'N700MS',
    'gs': 480,
    'alt_baro': 38000,
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
       patch('workers.overhead.TrackerLog') as mock_tracker_log_cls, \
       patch('workers.overhead.DatabaseManager') as mock_database_cls:

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


def grab_single_flight(overhead, flight, route=None):
  """Run _grab_data with a single chosen flight and return its data entry."""
  overhead._adsb_api.get_nearby_flights.return_value = [flight]
  overhead._flight_logic.choose_flight.return_value = (flight, route or {})
  overhead._grab_data()
  data = overhead.data
  assert len(data) == 1
  return data[0]


# Each of these registrations tokenizes to a code that exists in airlines.json
# (GAB -> Gendall Air, DAB -> Dassault Aviation, CGA -> Congressional Air), so
# without the registration check they'd be shown as that airline.
@pytest.mark.parametrize('callsign, registration', [
  ('GABCD', 'G-ABCD'),     # UK
  ('DABCD', 'D-ABCD'),     # Germany
  ('CGABC', 'C-GABC'),     # Canada
  ('GABCD   ', 'G-ABCD'),  # adsb.lol pads callsigns with trailing spaces
  ('gabcd', 'G-ABCD'),     # case differs
  ('GABCD', 'g-abcd'),
])
def test_registration_callsign_has_no_owner_icao(overhead, callsign, registration):
  entry = grab_single_flight(overhead, make_flight(flight=callsign, r=registration))

  assert entry['owner_icao'] == ''
  assert entry['airline'] == ''
  assert entry['owner_iata'] == 'N/A'


def test_us_registration_callsign_has_no_airline(overhead):
  """
  US N-numbers have no hyphen and already tokenize to '' — they should still
  end up with no airline name.
  """
  entry = grab_single_flight(overhead, make_flight(flight='N700MS  ', r='N700MS'))

  assert entry['owner_icao'] == ''
  assert entry['airline'] == ''
  assert entry['owner_iata'] == 'N/A'


@pytest.mark.parametrize('callsign, registration', [
  ('GABCD', 'G-ABCD'),
  ('GABCD   ', 'G-ABCD'),
  ('CGABC', 'C-GABC'),
  ('gabcd', 'G-ABCD'),
  ('N700MS  ', 'N700MS'),  # no hyphen to restore; padding is dropped
])
def test_registration_callsign_is_shown_as_registration(overhead, callsign, registration):
  entry = grab_single_flight(overhead, make_flight(flight=callsign, r=registration))

  assert entry['callsign'] == registration


def test_airline_callsign_is_not_replaced_by_registration(overhead):
  entry = grab_single_flight(overhead, make_flight(flight='BAW7CP', r='G-XWBA'))

  assert entry['callsign'] == 'BAW7CP'


def test_airline_callsign_is_tokenized_when_it_differs_from_registration(overhead):
  """A normal airline flight's callsign doesn't match its registration."""
  entry = grab_single_flight(overhead, make_flight(flight='BAW7CP  ', r='G-XWBA'))

  assert entry['owner_icao'] == 'BAW'
  assert entry['airline'] == 'British Airways'


def test_callsign_is_tokenized_when_registration_is_blank(overhead):
  """With no registration to compare against, fall back to tokenizing."""
  entry = grab_single_flight(overhead, make_flight(flight='BAW7CP', r=''))

  assert entry['owner_icao'] == 'BAW'
  assert entry['airline'] == 'British Airways'


def test_registration_check_does_not_match_on_prefix_only(overhead):
  """Only an exact match counts — a callsign that merely starts like the registration is still tokenized."""
  entry = grab_single_flight(overhead, make_flight(flight='GABCD1', r='G-ABCD'))

  assert entry['owner_icao'] == 'GAB'


@pytest.mark.parametrize('callsign, expected', [
  # Numeric flight numbers
  ('UAL123', 'UAL'),
  ('QTR8170', 'QTR'),
  ('DAL1', 'DAL'),
  # Flight numbers with letters after the ICAO (e.g. British Airways 7CP)
  ('BAW7CP', 'BAW'),
  ('EZY12AB', 'EZY'),
  ('RYR1JW', 'RYR'),
  ('SWA4A', 'SWA'),
  # ICAO only, no flight number
  ('BAW', 'BAW'),
])
def test_tokenize_airline_code_from_callsign_extracts_icao(callsign, expected):
  assert Overhead.tokenize_airline_code_from_callsign(callsign) == expected


@pytest.mark.parametrize('callsign, expected', [
  # adsb.lol pads callsigns with trailing spaces
  ('UAL123  ', 'UAL'),
  ('BAW7CP  ', 'BAW'),
  ('QTR8170\t', 'QTR'),
])
def test_tokenize_airline_code_from_callsign_ignores_trailing_whitespace(callsign, expected):
  assert Overhead.tokenize_airline_code_from_callsign(callsign) == expected


def test_tokenize_airline_code_from_callsign_preserves_case():
  # The method doesn't normalize case; callers get back what was in the callsign.
  assert Overhead.tokenize_airline_code_from_callsign('baw7cp') == 'baw'


@pytest.mark.parametrize('callsign', [
  '',             # blank callsign (BLANK_FIELDS are converted to '')
  '   ',          # whitespace only
  'UA',           # too short to hold a 3-letter ICAO
  'UA123',        # 2-letter (IATA-style) prefix
  'N123AB',       # US registration used as callsign
  '123ABC',       # starts with digits
  'U2L123',       # digit inside the ICAO portion
  ' UAL123',      # leading whitespace
  'UAL 123',      # whitespace inside the callsign
  'UAL-123',      # non-alphanumeric character
])
def test_tokenize_airline_code_from_callsign_returns_empty_when_no_icao(callsign):
  assert Overhead.tokenize_airline_code_from_callsign(callsign) == ''
