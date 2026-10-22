import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from config import DataSource
from services.adsbTracker import AdsbTrackerService

SCHEMA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app_data/routes_schema.sql'))

FEEDER_URL = '192.168.0.10:30152'
API_URL = 'opendata.adsb.fi'

@pytest.fixture(autouse=True)
def reset_singleton():
  '''AdsbTrackerService is a singleton; give each test a fresh instance.'''
  AdsbTrackerService._instance = None
  yield
  AdsbTrackerService._instance = None

def use_feeder(mock_config):
  mock_config.ADSB_DATA_SOURCE = DataSource.FEEDER
  mock_config.ADSB_DATA_URL = FEEDER_URL
  mock_config.ADSB_PAYLOAD_ROOT_KEY = 'aircraft'

def use_api(mock_config):
  mock_config.ADSB_DATA_SOURCE = DataSource.API
  mock_config.ADSB_DATA_URL = API_URL
  mock_config.ADSB_PAYLOAD_ROOT_KEY = 'ac'

@pytest.fixture
def mock_config():
  '''Patches config in both the service and the connection selector, defaulting to the feeder.'''
  mock_config = MagicMock()
  # Set APP_NAME to a string to avoid TypeError in logging.getLogger
  mock_config.APP_NAME = 'test_app'
  mock_config.ADSB_USER_AGENT = 'test-agent'
  mock_config.MIN_ALTITUDE = 1000
  use_feeder(mock_config)
  with patch('services.adsbTracker.config', mock_config), \
       patch('utils.httpConnectionSelector.config', mock_config):
    yield mock_config

@pytest.fixture
def mock_http_connection():
  with patch('utils.httpConnectionSelector.http.client.HTTPConnection') as mock_http_connection:
    yield mock_http_connection

@pytest.fixture
def mock_https_connection():
  with patch('utils.httpConnectionSelector.http.client.HTTPSConnection') as mock_https_connection:
    yield mock_https_connection

@pytest.fixture
def route_db(mock_config, tmp_path):
  '''A route database built from the real schema, with a few routes in it.'''
  db_file = str(tmp_path / 'routes.db')
  conn = sqlite3.connect(db_file)
  try:
    with open(SCHEMA_FILE) as f:
      conn.executescript(f.read())
    with conn:
      conn.executemany('INSERT INTO airports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [
        ('KLAX', 'KLAX', 'LAX', 'Los Angeles International Airport', 'Los Angeles', 'US', 33.942501, -118.407997, 125),
        ('KDEN', 'KDEN', 'DEN', 'Denver International Airport', 'Denver', 'US', 39.861698, -104.672997, 5434),
        ('KJFK', 'KJFK', 'JFK', 'John F Kennedy International Airport', 'New York', 'US', 40.639801, -73.7789, 13),
      ])
      conn.executemany('INSERT INTO route_stops VALUES (?, ?, ?)', [
        ('UAL1234', 0, 'KLAX'), ('UAL1234', 1, 'KDEN'), ('UAL1234', 2, 'KJFK'),
        ('DAL5', 0, 'KJFK'), ('DAL5', 1, 'KLAX'),
      ])
  finally:
    conn.close()

  mock_config.ROUTE_DB_FILE = db_file
  yield db_file

def make_response(status=200, body=b''):
  response = MagicMock()
  response.status = status
  response.read.return_value = body
  return response

def make_response(status=200, body=b''):
  response = MagicMock()
  response.status = status
  response.read.return_value = body
  return response

# get_nearby_flights

def test_get_nearby_flight_success(mock_config, mock_http_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({
    'aircraft': [
      {'alt_baro': 10000, 'dst': 5},
      {'alt_baro': 15000, 'dst': 3}
    ]
  }).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is not None
  assert len(result) == 2
  assert result[0]['alt_baro'] == 10000
  assert result[1]['alt_baro'] == 15000

def test_get_nearby_flights_feeder_uses_http_and_circle_query(mock_config, mock_http_connection, mock_https_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({'aircraft': []}).encode('utf-8'))

  service = AdsbTrackerService()
  service.get_nearby_flights(40.7128, -74.0060, 10)

  mock_http_connection.assert_called_once_with(host=FEEDER_URL, timeout=15)
  mock_https_connection.assert_not_called()
  path = mock_conn.request.call_args[0][1]
  assert path == '?circle=40.7128,-74.006,10'
  mock_conn.close.assert_called_once()

def test_get_nearby_flights_api_uses_https_and_v3_path(mock_config, mock_http_connection, mock_https_connection):
  use_api(mock_config)
  mock_conn = mock_https_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({'ac': []}).encode('utf-8'))

  service = AdsbTrackerService()
  service.get_nearby_flights(40.7128, -74.0060, 10)

  mock_https_connection.assert_called_once_with(host=API_URL, timeout=15)
  mock_http_connection.assert_not_called()
  path = mock_conn.request.call_args[0][1]
  assert path == '/api/v3/lat/40.7128/lon/-74.006/dist/10'
  mock_conn.close.assert_called_once()

def test_get_nearby_flights_api_reads_ac_key(mock_config, mock_https_connection):
  use_api(mock_config)
  mock_conn = mock_https_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({
    'ac': [{'alt_baro': 10000}, {'alt_baro': 'ground'}]
  }).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result == [{'alt_baro': 10000}]

def test_get_nearby_flights_drops_aircraft_without_numeric_altitude(mock_config, mock_http_connection):
  '''readsb reports 'ground' for alt_baro on the ground, and omits it when unknown.'''
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({
    'aircraft': [
      {'alt_baro': 10000},
      {'alt_baro': 'ground'},
      {'hex': 'abc123'},
    ]
  }).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result == [{'alt_baro': 10000}]

def test_get_nearby_flights_no_aircraft_field(mock_config, mock_http_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({}).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_feeder_ignores_ac_key(mock_config, mock_http_connection):
  '''The feeder (readsb) uses 'aircraft'; 'ac' belongs to the adsb.fi API.'''
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({
    'ac': [{'alt_baro': 10000}]
  }).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_api_ignores_aircraft_key(mock_config, mock_https_connection):
  use_api(mock_config)
  mock_conn = mock_https_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, json.dumps({
    'aircraft': [{'alt_baro': 10000}]
  }).encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_invalid_data_source_returns_none(mock_config, mock_http_connection, mock_https_connection):
  mock_config.ADSB_DATA_SOURCE = 'bogus'

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None
  mock_http_connection.assert_not_called()
  mock_https_connection.assert_not_called()

def test_get_nearby_flights_bad_status(mock_config, mock_http_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(400)

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_bad_json(mock_config, mock_http_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(200, 'bad json'.encode('utf-8'))

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_bad_status_logs_error(mock_config, mock_http_connection):
  mock_conn = mock_http_connection.return_value
  mock_conn.getresponse.return_value = make_response(503)

  service = AdsbTrackerService()
  with patch.object(service.logger, 'error') as mock_error:
    service.get_nearby_flights(40.7128, -74.0060, 10)
    mock_error.assert_called_once()
    assert '503' in mock_error.call_args[0][0]

def test_get_nearby_flights_connection_error_returns_none(mock_config, mock_http_connection):
  '''The data source being unreachable shouldn't raise into the grab thread.'''
  mock_http_connection.return_value.request.side_effect = ConnectionRefusedError('refused')

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None
  mock_http_connection.return_value.close.assert_called_once()

# get_routeset

def test_get_routeset_returns_stops_in_order_with_airport_details(route_db):
  service = AdsbTrackerService()
  result = service.get_routeset([{'flight': 'UAL1234'}])

  stops = result['UAL1234']
  assert [s['airport_icao'] for s in stops] == ['KLAX', 'KDEN', 'KJFK']
  assert [s['seq'] for s in stops] == [0, 1, 2]
  assert stops[1] == {
    'callsign': 'UAL1234',
    'seq': 1,
    'airport_icao': 'KDEN',
    'airport_iata': 'DEN',
    'airport_name': 'Denver International Airport',
    'airport_lat': 39.861698,
    'airport_lon': -104.672997,
    'airport_alt_feet': 5434,
  }

def test_get_routeset_strips_padded_callsigns(route_db):
  '''readsb pads callsigns to 8 characters with spaces.'''
  service = AdsbTrackerService()
  result = service.get_routeset([{'flight': 'DAL5    '}])

  assert [s['airport_icao'] for s in result['DAL5']] == ['KJFK', 'KLAX']

def test_get_routeset_looks_up_several_flights_and_leaves_out_unknown_callsigns(route_db):
  service = AdsbTrackerService()
  result = service.get_routeset([{'flight': 'UAL1234'}, {'flight': 'DAL5'}, {'flight': 'NOPE999'}])

  assert set(result) == {'UAL1234', 'DAL5'}

def test_get_routeset_skips_flights_without_a_callsign(route_db):
  '''readsb omits 'flight' until a callsign has been received.'''
  service = AdsbTrackerService()
  result = service.get_routeset([{'hex': 'abc123'}, {'flight': ''}, {'flight': 'DAL5'}])

  assert set(result) == {'DAL5'}

def test_get_routeset_without_callsigns_does_not_touch_the_database(mock_config):
  mock_config.ROUTE_DB_FILE = '/nonexistent/routes.db'
  service = AdsbTrackerService()

  with patch('services.adsbTracker.sqlite3.connect') as mock_connect:
    assert service.get_routeset([]) == {}
    assert service.get_routeset([{'hex': 'abc123'}]) == {}
    mock_connect.assert_not_called()

def test_get_routeset_handles_quotes_in_callsigns(route_db):
  '''Callsigns are passed as query parameters, so a quote can't break the query.'''
  service = AdsbTrackerService()
  result = service.get_routeset([{'flight': "O'BRIEN"}, {'flight': 'DAL5'}])

  assert set(result) == {'DAL5'}

def test_get_routeset_returns_empty_when_database_is_missing(mock_config, tmp_path):
  '''Before the first rebuild finishes there's no database yet.'''
  mock_config.ROUTE_DB_FILE = str(tmp_path / 'missing.db')
  service = AdsbTrackerService()

  with patch.object(service.logger, 'error') as mock_error:
    assert service.get_routeset([{'flight': 'UAL1234'}]) == {}
    mock_error.assert_called_once()

  assert not os.path.exists(mock_config.ROUTE_DB_FILE)  # read-only, so it isn't created

def test_get_routeset_returns_empty_when_file_is_not_a_database(mock_config, tmp_path):
  db_file = tmp_path / 'routes.db'
  db_file.write_bytes(b'this is not a database')
  mock_config.ROUTE_DB_FILE = str(db_file)

  service = AdsbTrackerService()
  assert service.get_routeset([{'flight': 'UAL1234'}]) == {}

# headers

def test_get_headers_contains_required_fields(mock_config):
  service = AdsbTrackerService()
  headers = service._get_headers()

  assert headers['Accept'] == 'application/json'
  assert headers['Content-Type'] == 'application/json'
