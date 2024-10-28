import config
import http.client
import json
import time

from service.authentication import AuthenticationService

'''
Default coordinates were taken from https://www.gps-coordinates.net/
'''

filepath = 'src/app_data/geo_cache.json'

class GeoService():
  def __init__(self):
    try:
      self.authentication = AuthenticationService()
      with open(filepath, 'r') as f:
        cached_location_data = json.load(f)
        current_timestamp = time.time() * 1000
        if round((current_timestamp - cached_location_data['timestamp']) / 1000 / 60) > config.LOCATION_CACHE_TIMEOUT:
          print(f'Location cache expired. Updating cache...')
          self._update_cache()
        else:
          self._location = [float(x) for x in cached_location_data['location']]
    except FileNotFoundError:
      print(f'Location cache not found. Building cache...')
      self._update_cache()

    except Exception:
      print(f'Error getting location data. Falling back to default coordinates: {config.LOCATION_COORDINATES_DEFAULT}')
      self._location = config.LOCATION_COORDINATES_DEFAULT

  # TODO use a try-catch to fall back onto the cache file if it exists.
  def _update_cache(self):
    token = self.authentication.get_rapidapi_token()

    if not token:
      return config.LOCATION_COORDINATES_DEFAULT

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
          print(f'Error getting location data. Falling back to expired cache...')
          cached_location_data = json.load(f)
          self._location = [float(x) for x in cached_location_data['location']]
      except FileNotFoundError:
        self._location = config.LOCATION_COORDINATES_DEFAULT
        print(f'Error getting location data. Falling back to default coordinates: {config.LOCATION_COORDINATES_DEFAULT}')

    with open('src/app_data/geo_cache.json', 'w') as f:
      json.dump({'location': self._location, 'timestamp': time.time() * 1000}, f)
    
  
  def get_home_lat(self):
    return self._location[0]

  def get_home_lon(self):
    return self._location[1]
  