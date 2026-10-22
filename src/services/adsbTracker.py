import sqlite3
import threading
import config
import json
import logging

from collections import defaultdict
from config import DataSource
from utils import httpConnectionSelector
from utils.timeUtils import TimeUtils
from http import HTTPStatus

EMPTY_ROUTESET = []

class AdsbTrackerService():
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(AdsbTrackerService, cls).__new__(cls)
      return cls._instance
  
  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    
    self.logger = logging.getLogger(config.APP_NAME)    

  def decode_response_payload(self, data: bytes):
    try:
      data_str = data.decode('utf-8')
      return json.loads(data_str)
    except json.JSONDecodeError as e:
      self.logger.error(f'Error decoding response payload: {e}')
      return None
  
  def _close(self, conn):
    if conn is None:
      return
    try:
      conn.close()
    except Exception:
      pass

  def _get_headers(self):
    return {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      'User-Agent': config.ADSB_USER_AGENT
    }
  
  def _get_nearby_flight_url(self, lat, lon, radius):
    match config.ADSB_DATA_SOURCE:
      case DataSource.API:
        return f'/api/v3/lat/{lat}/lon/{lon}/dist/{radius}'
      case DataSource.FEEDER:
        return f"?circle={lat},{lon},{radius}"
      case _:
        raise Exception("Invalid data source specified. Please update config.")

  # Gets nearby flights given a latitude, longitude, and radius in nautical miles.
  def get_nearby_flights(self, lat, long, radius, timeout=15):
    self.logger.info(f'Getting nearby flights')

    conn = None
    try:
      conn = httpConnectionSelector.getHttpConnectionType(url=config.ADSB_DATA_URL, timeout=timeout)
      conn.request('GET',
                    self._get_nearby_flight_url(lat, long, radius),
                    '',
                    self._get_headers())
      response = conn.getresponse()

      if response.status != HTTPStatus.OK:
        self.logger.error(f'Error getting flights. Response code: {response.status}. '
                          f'Body: {response.read().decode("utf-8", errors="replace").strip()}')
        return None

      data = self.decode_response_payload(response.read())

      if data is None or config.ADSB_PAYLOAD_ROOT_KEY not in data:
        return None

      try:
        filter_field = 'alt_baro'
        data = [x for x in data[config.ADSB_PAYLOAD_ROOT_KEY] if filter_field in x and type(x[filter_field]) is int]
      except KeyError as e:
        with open('error_log.json', 'w') as f:
          json.dump(data, f)
        return None

      # return sorted(data, key=lambda x: x['dst'])
      return data

    except Exception as e:
      self.logger.error(f'Error getting nearby flights: {e}')
      return None

    finally: # always release the socket, including on the early returns above
      self._close(conn)


  # Looks up the routes of a list of flights by callsign in the local route database.
  # Returns {callsign: [stop, ...]} with each route's stops in order, so [0] is the
  # origin and [-1] is the final destination. Callsigns with no route are left out.
  # Returns {} if the database can't be read, e.g. before it's first been built.
  def get_routeset(self, flights):
    callsigns = [flight['flight'].strip() for flight in flights if flight.get('flight')]
    if not callsigns:
      return {}

    conn = None
    try:
      conn = sqlite3.connect(f'file:{config.ROUTE_DB_FILE}?mode=ro', uri=True)
      conn.row_factory = sqlite3.Row
      rows = conn.execute(f'''
        select
          rs.callsign     as callsign,
          rs.seq          as seq,
          rs.airport_code as airport_icao,
          a.iata          as airport_iata,
          a.name          as airport_name,
          a.lat           as airport_lat,
          a.lon           as airport_lon,
          a.alt_feet      as airport_alt_feet
        from route_stops rs
        inner join airports a on a.code = rs.airport_code
        where rs.callsign in ({','.join('?' * len(callsigns))})
        order by rs.callsign, rs.seq
      ''', callsigns).fetchall()
    except sqlite3.Error as e:
      self.logger.error(f'Error looking up routes: {e}')
      return {}
    finally:
      if conn is not None:
        conn.close()

    routes = defaultdict(list)
    for row in rows:
      routes[row['callsign']].append(dict(row))
    return routes

