import http.client
import config
import json
import logging

from http import HTTPStatus

# from authentication import AuthenticationService


class AdsbTrackerService():
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    with open('src/app_data/routeset_default.json', 'r') as f:
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
  def get_routeset(self, lat=0, long=0, callsign=''):
    self.logger.info(f'Getting route for {callsign}')
  
    if not callsign:
      return self._default_routeset
    try:
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
      
      if response.status != HTTPStatus.OK:
        return self._default_routeset

      data = self.decode_response_payload(response.read())

      conn.close()

      if data is None or len(data[0]['_airports']) == 0:
        return self._default_routeset
      
      return data[0]
    except Exception as e:
      self.logger.error(f'Error getting routeset: {e}')
      try: # attempt to close the connection if it's open
        conn.close()
      except Exception:
        pass
      return self._default_routeset
