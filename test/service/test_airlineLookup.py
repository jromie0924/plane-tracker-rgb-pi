import json
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from services.airlineLookup import AirlineLookupService

# Constants
AIRLINES_JSON_PATH = 'src/app_data/airlines.json'
REQUIRED_FIELDS = ['id', 'name', 'alias', 'iata', 'icao', 'callsign', 'country', 'active']

def test_airlines_json_valid():
  """Test that airlines.json is valid JSON and can be loaded"""
  with open(AIRLINES_JSON_PATH, 'r') as f:
    data = json.load(f)
  
  assert isinstance(data, list)
  assert len(data) > 0

def test_airlines_json_structure():
  """Test that each airline entry has required fields"""
  with open(AIRLINES_JSON_PATH, 'r') as f:
    data = json.load(f)
  
  # Check first and last entries have required fields
  for airline in [data[0], data[-1]]:
    for field in REQUIRED_FIELDS:
      assert field in airline, f"Missing field '{field}' in airline entry"

def test_lookup_air_premia():
  """Test that Air Premia (APZ) can be looked up"""
  service = AirlineLookupService()
  result = service.lookup('APZ')
  
  assert result == 'Air Premia'

def test_lookup_air_premia_lowercase():
  """Test that Air Premia lookup is case-insensitive"""
  service = AirlineLookupService()
  result = service.lookup('apz')
  
  assert result == 'Air Premia'

def test_lookup_well_known_airlines():
  """Spot check several well-known airlines"""
  service = AirlineLookupService()
  
  # Test a few well-known airlines by ICAO code
  test_cases = [
    ('UAL', 'United Airlines'),
    ('AAL', 'American Airlines'),
    ('DAL', 'Delta Air Lines'),
    ('SWA', 'Southwest Airlines'),
  ]
  
  for icao, expected_name in test_cases:
    result = service.lookup(icao)
    assert result == expected_name, f"Expected '{expected_name}' for ICAO '{icao}', got '{result}'"

def test_lookup_nonexistent_airline():
  """Test that lookup returns empty string for non-existent airline"""
  service = AirlineLookupService()
  result = service.lookup('ZZZZZ')
  
  assert result == ''

def test_lookup_empty_string():
  """Test that lookup handles empty string gracefully"""
  service = AirlineLookupService()
  result = service.lookup('')
  
  # The lookup returns a string (empty or not), not an error
  assert isinstance(result, str)

def test_air_premia_icao_unique_among_active():
  """Test that Air Premia's ICAO code (APZ) is unique among active airlines"""
  with open(AIRLINES_JSON_PATH, 'r') as f:
    data = json.load(f)
  
  # Count how many active airlines have ICAO code 'APZ'
  apz_count = sum(1 for airline in data if airline['active'] == 'Y' and airline['icao'] == 'APZ')
  
  # Air Premia should be the only active airline with ICAO code APZ
  assert apz_count == 1, f"Expected 1 active airline with ICAO 'APZ', found {apz_count}"

def test_air_premia_entry_complete():
  """Test that Air Premia entry has all expected fields filled correctly"""
  with open(AIRLINES_JSON_PATH, 'r') as f:
    data = json.load(f)
  
  # Find Air Premia using a generator expression for efficiency
  air_premia = next((airline for airline in data if airline['icao'] == 'APZ'), None)
  
  assert air_premia is not None, "Air Premia not found in database"
  assert air_premia['name'] == 'Air Premia'
  assert air_premia['iata'] == 'YP'
  assert air_premia['icao'] == 'APZ'
  assert air_premia['callsign'] == 'AIR PREMIA'
  assert air_premia['country'] == 'South Korea'
  assert air_premia['active'] == 'Y'
