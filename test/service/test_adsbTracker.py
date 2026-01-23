import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from services.adsbTracker import AdsbTrackerService

@pytest.fixture
def mock_config():
  with patch('services.adsbTracker.config') as mock_config:
    # Set APP_NAME to a string to avoid TypeError in logging.getLogger
    mock_config.APP_NAME = 'test_app'
    yield mock_config

@pytest.fixture
def mock_https_connection():
  with patch('services.adsbTracker.http.client.HTTPSConnection') as mock_https_connection:
    yield mock_https_connection

def test_get_nearby_flight_success(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.read.return_value = json.dumps({
    'ac': [
      {'alt_baro': 10000, 'dst': 5},
      {'alt_baro': 15000, 'dst': 3}
    ]
  }).encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is not None
  assert len(result) == 2
  assert result[0]['alt_baro'] == 10000
  assert result[1]['alt_baro'] == 15000

def test_get_nearby_flights_no_ac_field(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.read.return_value = json.dumps({}).encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_bad_status(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 400
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_bad_json(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.read.return_value = 'bad json'.encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_nearby_flights_missing_ac_key(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.read.return_value = json.dumps({
    'some_other_key': []
  }).encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  result = service.get_nearby_flights(40.7128, -74.0060, 10)

  assert result is None

def test_get_routeset_success(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.read.return_value = json.dumps([{
    'callsign': 'test_callsign',
    '_airports': ['JFK']
  }]).encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  flights = [{'flight': 'test_callsign', 'lat': 40.7128, 'lon': -74.0060}]
  result = service.get_routeset(flights)

  assert result is not None
  assert len(result) == 1
  assert result[0]['route']['_airports'][0] == 'JFK'


def test_get_routeset_no_callsign(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.read.return_value = json.dumps([{
    'callsign': '',
    '_airports': ['JFK']
  }]).encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  flights = [{'flight': '', 'lat': 40.7128, 'lon': -74.0060}]
  result = service.get_routeset(flights)

  # Empty callsign matches empty callsign
  assert len(result) == 1
  assert result[0]['route']['callsign'] == ''

def test_get_routeset_bad_status(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 400
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  flights = [{'flight': 'test_callsign', 'lat': 40.7128, 'lon': -74.0060}]
  result = service.get_routeset(flights)

  # Bad status returns empty routeset
  assert result == []


def test_get_routeset_bad_json(mock_config, mock_https_connection):
  mock_config.ADSB_LOL_URL = 'test_url'
  mock_conn = mock_https_connection.return_value
  mock_response = MagicMock()
  mock_response.status = 200
  mock_response.read.return_value = 'bad json'.encode('utf-8')
  mock_conn.getresponse.return_value = mock_response

  service = AdsbTrackerService()
  flights = [{'flight': 'test_callsign', 'lat': 40.7128, 'lon': -74.0060}]
  result = service.get_routeset(flights)

  # Bad JSON causes exception, returns empty routeset
  assert result == []