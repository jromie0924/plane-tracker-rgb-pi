import http.client
import config
import json

from authentication import AuthenticationService


class AdsbTrackerService():
  def __init__(self):
    auth = AuthenticationService()
    self._fr24_api_token = auth.flightradar24_token
    self.conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)

  def decode_response_payload(self, data: bytes):
    data_str = data.decode('utf-8')
    return json.loads(data_str)
  
  def _get_headers(self):
    return {
      'Accept': 'application/json'
    }
  
  def _get_closest_flight_url(self, lat, long, radius):
    return f'/v2/closest/{lat}/{long}/{radius}'
  

  def _get_routeset_url(self, lat, long, callsign):
    return '/api/0/routeset'
  

  def get_closest_flight(self, lat, long, radius):
    self.conn.request('GET',
                      self._get_closest_flight_url(lat, long, radius),
                      payload='',
                      headers=self._get_headers())
    response = self.conn.getresponse()
    return self.decode_response_payload(response.read())


  def get_routeset(self, lat, long, callsign: str):
    payload = {
      "planes": [
        {
          "callsign": callsign,
          "lat": lat,
          "long": long
        }
      ]
    }

    self.conn.request('POST',
                      self._get_closest_flight_url(lat, long, callsign),
                      payload=payload,
                      headers=self._get_headers())
    
    response = self.conn.getresponse()
    return self.decode_response_payload(response.read())
