import http.client
import config
import json
import logging

# from authentication import AuthenticationService


class AdsbTrackerService():
  def __init__(self):
    # # TODO: Uncomment, and fill the token value with the auth token in the auth service.
    # # This won't be necessary until the adsb.lol service requires API tokens.
    # auth = AuthenticationService()
    # self._fr24_api_token = auth.flightradar24_token
    self.conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
    self.logger = logging.getLogger(__name__)
    with open('src/app_data/loc_default.json', 'r') as f:
      self._default_routeset = json.load(f)

  def decode_response_payload(self, data: bytes):
    data_str = data.decode('utf-8')
    return json.loads(data_str)
  
  def _get_headers(self):
    return {
      'Accept': 'application/json'
    }
  
  def _get_nearby_flight_url(self, lat, long, radius):
    return f'/v2/point/{lat}/{long}/{radius}'
  

  def _get_routeset_url(self):
    return '/api/0/routeset'
  

  def get_nearby_flight(self, lat, long, radius):
    self.logger.info(f'Retrieving nearby flight information for latitude {lat}, longitude {long}, radius {radius}')
    self.conn.request('GET',
                      self._get_nearby_flight_url(lat, long, radius),
                      '',
                      self._get_headers())
    response = self.conn.getresponse()
    data = self.decode_response_payload(response.read())
    
    data = [x for x in data['ac'] if x['hex'][0] != '~' and x['alt_baro'] != 'ground']

    return sorted(data, key=lambda aircraft: aircraft['dst'])


  def get_routeset(self, lat=0, long=0, callsign=''):
    self.logger.info(f'Retrieving route for flight {callsign}')
    if not callsign:
      return self._default_routeset

    payload = {
      "planes": [
        {
          "callsign": callsign.strip(),
          "lat": lat,
          "lng": long
        }
      ]
    }

    self.conn.request('POST',
                      self._get_routeset_url(),
                      json.dumps(payload),
                      self._get_headers())
    
    response = self.conn.getresponse()
    data = self.decode_response_payload(response.read())

    if len(data[0]['_airports']) == 0:
      return self._default_routeset
    
    return data[0]
