import json
import threading

LOOKUP_FILE = 'app_data/airlines.json'

class AirlineLookupService:
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(AirlineLookupService, cls).__new__(cls)
      return cls._instance
  
  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    
    with open(LOOKUP_FILE, 'r') as f:
      self._data = json.load(f)
  
  def lookup(self, code: str):
    results = [airline for airline in self._data if airline['icao'] == code.upper()]
    if len(results):
      return results[0]['name']
    
    return ''