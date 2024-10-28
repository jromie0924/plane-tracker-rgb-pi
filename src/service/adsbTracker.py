import http.client
import config
import json
import logging
import threading

from time import sleep

# from authentication import AuthenticationService


class AdsbTrackerService():
  def __init__(self):
    # # TODO: Uncomment, and fill the token value with the auth token in the auth service.
    # # This won't be necessary until the adsb.lol service requires API tokens.
    # auth = AuthenticationService()
    # self._fr24_api_token = auth.flightradar24_token
    # self.conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
    self.logger = logging.getLogger(__name__)
    with open('src/app_data/loc_default.json', 'r') as f:
      self._default_routeset = json.load(f)

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
    print(f'Thread ID {threading.current_thread().ident} inside get_nearby_flight()')
    print(f'number of threads: {threading.active_count()}')
    conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
    conn.request('GET',
                      self._get_nearby_flight_url(lat, long, radius),
                      '',
                      self._get_headers())
    response = conn.getresponse()

    if response.status != 200:
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


  # Attempts to get the route of an airplane by callsign
  # The lat & long values are used to calculate a plausibility of the route.
  def get_routeset(self, lat=0, long=0, callsign=''):
    # self.logger.info(f'Retrieving route for flight {callsign}')
    print(f'Thread ID {threading.current_thread().ident} inside get_routeset()')
    print(f'number of threads: {threading.active_count()}')
    if not callsign:
      return self._default_routeset
    
    conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)

    payload = {
      "planes": [
        {
          "callsign": callsign.strip(),
          "lat": lat,
          "lng": long
        }
      ]
    }

    conn.request('POST',
                      self._get_routeset_url(),
                      json.dumps(payload),
                      self._get_headers())
    
    response = conn.getresponse()
    
    if response.status != 200:
      return self._default_routeset

    data = self.decode_response_payload(response.read())

    conn.close()

    if data is None or len(data[0]['_airports']) == 0:
      return self._default_routeset
    
    return data[0]
