import http.client
import config
import json
import logging
import time

from utils.timeUtils import TimeUtils
from http import HTTPStatus

# from authentication import AuthenticationService
EMPTY_ROUTESET = []

class AdsbTrackerService():
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    with open('src/app_data/routeset_default.json', 'r') as f:
      self._default_routeset = json.load(f)
    
    self._routeset_timestamp = TimeUtils.current_time_milli()

  def decode_response_payload(self, data: bytes):
    try:
      data_str = data.decode('utf-8')
      return json.loads(data_str)
    except json.JSONDecodeError as e:
      self.logger.error(f'Error decoding response payload: {e}')
      return None
  
  def _get_headers(self):
    return {
      'Accept': 'application/json'
    }
  
  def _get_nearby_flight_url(self, lat, long, radius):
    return f'/v2/point/{lat}/{long}/{radius}'
  

  def _get_routeset_url(self):
    return '/api/0/routeset'
  

  # Gets nearby flights given a latitude, longitude, and radius in nautical miles.
  def get_nearby_flights(self, lat, long, radius):
    self.logger.info(f'Getting nearby flights')

    try:
      conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
      conn.request('GET',
                        self._get_nearby_flight_url(lat, long, radius),
                        '',
                        self._get_headers())
      response = conn.getresponse()

      if response.status != HTTPStatus.OK:
        return None
      
      data = self.decode_response_payload(response.read())

      if data is None or 'ac' not in data:
        return None
      
      try:
        filter_field = 'alt_baro'
        data = [x for x in data['ac'] if filter_field in x and type(x[filter_field]) is int]
      except KeyError as e:
        with open('error_log.json', 'w') as f:
          json.dump(data, f)
        return None

      conn.close()

      # return sorted(data, key=lambda x: x['dst'])
      return data

    except Exception as e:
      self.logger.error(f'Error getting nearby flights: {e}')
      try: # attempt to close the connection if it's open
        conn.close()
      except Exception:
        pass
      return None


  # Attempts to get the route of an airplane by callsign
  # The lat & long values are used to calculate a plausibility of the route.
  def get_routeset(self, flights):
    # self.logger.info(f'Getting route for {callsign}')
    # '''
    # Rate limiter for routeset endpoint.
    # The FlightLogic class will call this method for multiple flights,
    # and this is a preventative measure to prevent the ADSB.lol API developer
    # from not liking me.
    # '''
    # now = TimeUtils.current_time_milli()
    # while now - self._routeset_timestamp < config.ROUTESET_LIMIT_SECONDS * 1000:
    #   self.logger.warning(f'Rate limiting routeset endpoint. Waiting {config.ROUTESET_LIMIT_SECONDS} second...')
    #   time.sleep(1)
    #   now = TimeUtils.current_time_milli()
    
    payload = {'planes': []}
      
      
    for flight in flights:
      callsign = flight['flight']
      lat = flight['lat']
      long = flight['lon']
      # self.logger.info(f'Getting route for {callsign}')
      payload['planes'].append({
        'callsign': callsign.strip(),
        'lat': lat,
        'lng': long
      })
  
    # if not callsign:
    #   return self._default_routeset
    # try:
    #   conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)

    #   payload = {
    #     "planes": [
    #       {
    #         "callsign": callsign.strip(),
    #         "lat": lat,
    #         "lng": long
    #       }
    #     ]
    #   }
    
    try:
      conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
      conn.request('POST',
                        self._get_routeset_url(),
                        json.dumps(payload),
                        self._get_headers())
      
      response = conn.getresponse()
      
      if response.status != HTTPStatus.OK:
        # return self._default_routeset
        return EMPTY_ROUTESET

      data = self.decode_response_payload(response.read())

      conn.close()
      
      data = [x for x in data if x['_airports'] and len(x['_airports']) > 0]

      # if data is None or len(data[0]['_airports']) == 0:
      #   # return self._default_routeset
      #   return EMPTY_ROUTESET
      
      # return data[0]
      
      merged_data = []
      for flight in flights:
        for route in data:
          if flight['flight'].strip() == route['callsign'].strip():
            merged_data.append({
              'flight': flight,
              'route': route
            })
      return merged_data
      
      
    except Exception as e:
      self.logger.error(f'Error getting routeset: {e}')
      try: # attempt to close the connection if it's open
        conn.close()
      except Exception:
        pass
      # return self._default_routeset
      return EMPTY_ROUTESET
