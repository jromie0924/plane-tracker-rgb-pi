import json

LOOKUP_FILE = 'src/app_data/airlines.json'

class AirlineLookupService:
  def __init__(self):
    with open(LOOKUP_FILE, 'r') as f:
      self._data = json.load(f)
  
  def lookup(self, code: str):
    results = [airline for airline in self._data if airline['icao'] == code.upper()]
    if len(results):
      return results[0]['name']
    
    return ''