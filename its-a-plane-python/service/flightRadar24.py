import http.client
import config
import json

from authentication import AuthenticationService


class FlightRadar24Service:
  def __init__(self):
    auth = AuthenticationService()
    self._fr24_api_token = auth.flightradar24_token
    self.conn = http.client.HTTPSConnection(config.FLIGHTRADAR24_URL)

  def _get_headers(self):
    return {
      'Accept': 'application/json',
      'Accept-Version': 'v1',
      'Authorization': f'Bearer {self._fr24_api_token}'
    }
  
  def _get_flight_positions_live_url(query_string=''):
    return f'/api{'' if config.LIVE else '/sandbox'}/live/flight-positions/full?{query_string}'
  
  def get_flights(self, bounds='50.682,46.218,14.422,22.243'):
    self.conn.request('GET',
                      self._get_flight_positions_live_url(f'bounds={bounds}'),
                      payload='',
                      headers=self._get_headers())
    response = self.conn.getresponse()
    data = response.read().decode('utf-8')
    
    return json.loads(data)
