import config
import geopy.distance as geodistance

from geopy.geocoders import Nominatim

'''
Default coordinates were taken from https://www.gps-coordinates.net/
'''

class GeoUtils():
  def __init__(self):
    try:
      geolocator = Nominatim(user_agent='bad_hombres_plane_tracker')
      self.location = geolocator.geocode(config.LOCATION)

    except Exception:
      # Default to a 30 mile (diagonal) radius from the center of Chicago
      self._bounds = [
        41.9267684604688,
        -87.69301898128884,
        41.82431337321679,
        -87.55593288861269
      ]

      self._location = [41.8755616, -87.6244212]

  
  def get_bounds(self):
    return self._bounds