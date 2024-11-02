import config
import http.client
import json
import time
import logging

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

class GeoService():
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self._location = []
    try:
      self.authentication = AuthenticationService()
      with open(filepath, 'r') as f:
        cached_location_data = json.load(f)
        current_timestamp = time.time() * 1000
        if round((current_timestamp - cached_location_data['timestamp']) / 1000 / 60) > config.LOCATION_CACHE_TIMEOUT:
          self.logger.warning(f'Location cache expired. Updating cache...')
          self._update_cache()
        else:
          self._location = [float(x) for x in cached_location_data['location']]
    except FileNotFoundError:
      self.logger.info(f'Location cache not found. Building cache...')
      self._update_cache()

    except Exception:
      self.logger.error(f'Error getting location data. Falling back to default coordinates: {config.LOCATION_COORDINATES_DEFAULT}')
      self._location = config.LOCATION_COORDINATES_DEFAULT

  def _update_cache(self):
    token = self.authentication.get_rapidapi_token()

    if not token:
      self._location = config.LOCATION_COORDINATES_DEFAULT
      return

    headers = {
      'x-rapidapi-key': token,
      'x-rapidapi-host': config.RAPIDAPI_HOST
    }

    endpoint = f'/v1/forward?format=json&street={config.STREET}&city={config.CITY}&state={config.STATE}&postalcode={config.ZIP_CODE}&country={config.COUNTRY}'\
                f'&accept-language=en&addressdetails=1&limit=1&bounded=0&polygon_text=0&polygon_kml=0&polygon_svg=0&polygon_geojson=0&polygon_threshold=0.0'

    try:
      conn = http.client.HTTPSConnection(config.RAPIDAPI_HOST)
      conn.request("GET", endpoint.replace(' ', '%20'), headers=headers)
      res = conn.getresponse()

      if res.status == 200:
        data = res.read().decode('utf-8')
        location_data = json.loads(data)
        # return [location_data[0]['lat'], location_data[0]['lon']]
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
      json.dump({'location': self._location, 'timestamp': time.time() * 1000}, f)
    
  @property
  def location(self):
    return self._location

  @property
  def latitude(self):
    return self._location[0]

  @property
  def longitude(self):
    return self._location[1]
  