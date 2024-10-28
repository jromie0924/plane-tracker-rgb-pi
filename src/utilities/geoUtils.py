import config
import json
import time
import geopy.distance as geodistance

from geopy.geocoders import Nominatim

'''
Default coordinates were taken from https://www.gps-coordinates.net/
'''

class GeoUtils():
  def __init__(self):
    try:
      filepath = 'src/app_data/geo_cache.json'
      with open(filepath, 'r') as f:
        cached_location_data = json.load(f)
        current_timestamp = time.time() * 1000
        if round((current_timestamp - cached_location_data['timestamp']) / 1000 / 60) > config.LOCATION_CACHE_TIMEOUT: # TODO: fix this
          self._location = self.update_cache()
        else:
          self._location = cached_location_data['location']
    
    except FileNotFoundError:
      self._location = self.update_cache()

    except Exception:
      # Default coordinates
      self._location = [41.8755616, -87.6244212]

  def update_cache(self):
    user_agent = 'bad_hombres_flight_tracker'
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(config.LOCATION)
    with open('src/app_data/geo_cache.json', 'w') as f:
      json.dump({
        'location': [location.latitude, location.longitude],
        'timestamp': int(time.time() * 1000)
      }, f)
    return [location.latitude, location.longitude]
  
  def get_home_lat(self):
    return self._location[0]

  def get_home_lon(self):
    return self._location[1]
  