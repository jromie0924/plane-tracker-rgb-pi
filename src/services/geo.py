import config
import http.client
import json
import logging
import os
import threading

from http import HTTPStatus
from utils.timeUtils import TimeUtils
from services.authentication import AuthenticationService

'''
This class uses a cache file to store the home location coordinates.
If the cache file is not found, or if the cache has expired, the class
will make a request to the RapidAPI Geocoding API to get the home
location coordinates. The class will then update the cache file with
the new coordinates.

This is to prevent making unnecessary requests to the RapidAPI
Geocoding service.
'''

filepath = 'src/app_data/geo_cache.json'

'''
Singleton class
'''
class GeoService():
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(GeoService, cls).__new__(cls)
        cls._instance.__init__()
      return cls._instance
  
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self._location = []
    if not config.LOCATION_COORDINATES_OVERRIDE:
      try:
        self.authentication = AuthenticationService()
        with open(filepath, 'r') as f:
          cached_location_data = json.load(f)
          current_timestamp = TimeUtils.current_time_milli()
          if round((current_timestamp - cached_location_data['timestamp']) / 1000 / 60) > config.LOCATION_CACHE_TIMEOUT:
            self.logger.warning(f'Location cache expired. Updating cache...')
            self._update_cache()
          else:
            self._location = [float(x) for x in cached_location_data['location']]
      except FileNotFoundError:
        self.logger.info(f'Location cache not found. Building cache...')
        self._update_cache()

      except Exception as e:
        self.logger.error(f'Error getting location data. Falling back to default coordinates: {config.LOCATION_COORDINATES_DEFAULT}')
        self._location = config.LOCATION_COORDINATES_DEFAULT
        raise e
    else:
      self.logger.warning(f'Location coordinates override detected. Using override coordinates: {config.LOCATION_COORDINATES_OVERRIDE}')
      self._location = config.LOCATION_COORDINATES_OVERRIDE
      try:
        os.remove(filepath)
      except FileNotFoundError:
        pass

  def _update_cache(self):
    token = self.authentication.rapidapi_token

    if not token:
      self._location = config.LOCATION_COORDINATES_DEFAULT
      return

    headers = {
      'x-rapidapi-key': token,
      'x-rapidapi-host': config.RAPIDAPI_HOST
    }

    endpoint = f'/v1/forward?format=json&postalcode={config.ZIP_CODE}&country={config.COUNTRY}'\
                f'&accept-language=en&addressdetails=1&limit=1&bounded=0&polygon_text=0&polygon_kml=0'\
                f'&polygon_svg=0&polygon_geojson=0&polygon_threshold=0.0'

    try:
      conn = http.client.HTTPSConnection(config.RAPIDAPI_HOST)
      conn.request("GET", endpoint.replace(' ', '%20'), headers=headers)
      res = conn.getresponse()

      if res.status == HTTPStatus.OK:
        data = res.read().decode('utf-8')
        location_data = json.loads(data)
        self._location = [float(location_data[0]['lat']), float(location_data[0]['lon'])]
      else:
        self._location = config.LOCATION_COORDINATES_DEFAULT
    except Exception as e:
      try:
        with open(filepath, 'r') as f:
          self.logger.error(f'Error getting location data. Falling back to expired cache...')
          cached_location_data = json.load(f)
          self._location = [float(x) for x in cached_location_data['location']]
      except FileNotFoundError:
        self._location = config.LOCATION_COORDINATES_DEFAULT
        self.logger.error(f'Error getting location data. Falling back to default coordinates: {config.LOCATION_COORDINATES_DEFAULT}')

    with open('src/app_data/geo_cache.json', 'w') as f:
      json.dump({'location': self._location, 'timestamp': TimeUtils.current_time_milli()}, f)
    
  @property
  def location(self):
    return self._location

  @property
  def latitude(self):
    return self._location[0]

  @property
  def longitude(self):
    return self._location[1]
  