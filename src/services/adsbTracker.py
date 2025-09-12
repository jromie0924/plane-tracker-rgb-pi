import http.client

import timeout_decorator
import config
import json
import logging
import time
import socket

from utils.timeUtils import TimeUtils
from http import HTTPStatus

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
  @timeout_decorator.timeout(seconds=10, use_signals=False)
  def get_nearby_flights(self, lat, long, radius):
    self.logger.info(f'Getting nearby flights')
    retries = 0
    
    while retries < config.MAX_RETRIES:
      try:
        self.logger.debug("Creating HTTPS Connection...")
        conn = http.client.HTTPSConnection(config.ADSB_LOL_URL, timeout=5)
        self.logger.debug("Connection established. Requesting flight data...")
        conn.request('GET',
                      self._get_nearby_flight_url(lat, long, radius),
                      '',
                      self._get_headers())
        response = conn.getresponse()
        self.logger.debug("response received")

        if response.status != HTTPStatus.OK:
          self.logger.error(f"Server error retrieving flights, HTTP status {response.status}")
          return None
        
        data = self.decode_response_payload(response.read())

        if data is None or 'ac' not in data:
          self.logger.info("No flights found")
          return None
        
        self.logger.debug("Response was successful.")
        
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
      
      except socket.timeout:
        retries += 1
        self.logger.error(f"Connection timed out. Retrying {retries} of {config.MAX_RETRIES} allowable attempts...")
        try: # attempt to close the connection if it's open
          conn.close()
        except Exception:
          pass
      except Exception as e:
        self.logger.error(f'Error getting nearby flights: {e}')
        try: # attempt to close the connection if it's open
          conn.close()
        except Exception:
          pass
        return None


  # Attempts to get the routes of a list of flights by callsign.
  def get_routeset(self, flights):
    payload = {'planes': []}
    
    for flight in flights:
      callsign = flight['flight']
      lat = flight['lat']
      long = flight['lon']
      payload['planes'].append({
        'callsign': callsign.strip(),
        'lat': lat,
        'lng': long
      })
  
    try:
      conn = http.client.HTTPSConnection(config.ADSB_LOL_URL)
      conn.request('POST',
                        self._get_routeset_url(),
                        json.dumps(payload),
                        self._get_headers())
      
      response = conn.getresponse()
      
      if response.status != HTTPStatus.OK:
        return EMPTY_ROUTESET

      data = self.decode_response_payload(response.read())

      conn.close()
      
      data = [x for x in data if x['_airports'] and len(x['_airports']) > 0]
      
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
      return EMPTY_ROUTESET
