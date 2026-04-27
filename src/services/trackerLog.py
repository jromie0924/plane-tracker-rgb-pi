import threading
import config
import logging
import json
import os

from utils.timeUtils import TimeUtils

class TrackerLog:
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(TrackerLog, cls).__new__(cls)
      return cls._instance
  
  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    self.logger = logging.getLogger(config.APP_NAME)
    self._last_save_time = round(TimeUtils.current_time_milli())
    self.data = self._load_file()
    self.cleanse_log()
    
  def cleanse_log(self):
    self.data = {k:v for k, v in self.data.items() if round(TimeUtils.current_time_milli()) - v.get('timestamp') < config.TRACKER_LOG_TTL_HOURS * 60 * 60 * 1000}
    self.save_file()
    
  def update_log(self, entries: list[dict]):
    current_timestamp = TimeUtils.current_time_milli()
    for entry in entries:
      entry['timestamp'] = current_timestamp
      try:
        entry_callsign: str = entry.get('flight') or entry.get('r')
        entry_callsign = entry_callsign.strip()
      except AttributeError:
        self.logger.warning(f'Entry {entry} does not have an identifier. Flight will not be logged.')
        continue
      
      self.data[entry_callsign] = entry
      
    self.cleanse_log()
    
  def _load_file(self) -> dict:
    filepath = config.TRACKER_LOG_FILE
    try:
      with open(filepath, 'r') as file:
        data = json.load(file)
        return data
    except FileNotFoundError:
      return {}
    
  def save_file(self, overwrite=False) -> bool:
    now = round(TimeUtils.current_time_milli())
    if now - self._last_save_time < config.TRACKER_LOG_SAVE_INTERVAL_MINUTES * 60 * 1000 and not overwrite:
      return True

    self.logger.info("Saving in-memory tracker log to file")
    filepath = config.TRACKER_LOG_FILE
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
      with open(filepath, 'w') as file:
        json.dump(self.data, file, indent=None)
      self._last_save_time = now
      return True
    except Exception:
      self.logger.error(f'Exception encountered while saving tracker log file.', exc_info=True)
      return False