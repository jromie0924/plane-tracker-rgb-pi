import threading
import config
import logging
import boto3
from botocore.exceptions import ClientError

from decimal import Decimal
from datetime import datetime
from services.adsbTracker import AdsbTrackerService
from services.flightLogic import FlightLogic
from services.singleton import Singleton
from utils.timeUtils import TimeUtils
from services.runtime import RuntimeService
from setup.screen import IS_RASPBERRY_PI

_DYNAMODB_TABLE_NAME = 'tracker_log' if IS_RASPBERRY_PI else 'tracker_log_emu'


class TrackerLog(Singleton):
  def __init__(self):
    self._adsb_service = AdsbTrackerService()
    self._flight_logic = FlightLogic()
    self._write_lock = threading.Lock()
    
    # Feature flag for emulator logging    
    self._tracker_log_active = IS_RASPBERRY_PI or config.TRACKER_LOG_EMU_FLAG

    self.logger = logging.getLogger(config.APP_NAME)
    self.logger.info(f'{self.__class__.__name__} successfully initialized.')
    self.logger.info(f'DynamoDB tracker log service active: {self._tracker_log_active}')
    
    runtime = RuntimeService()
    self._table = boto3.resource(
      'dynamodb',
      aws_access_key_id=runtime.aws_access_key_id,
      aws_secret_access_key=runtime.aws_secret_access_key,
      region_name=config.AWS_REGION
    ).Table(_DYNAMODB_TABLE_NAME)

  def update_log(self, entries: list[dict]):
    with self._write_lock:
      self._update_log(entries=entries)

  def _update_log(self, entries: list[dict]):
    if self._tracker_log_active:
      current_timestamp = TimeUtils.current_time_milli()
      expires_at = int(current_timestamp / 1000) + config.TRACKER_LOG_TTL_HOURS * 3600

      items = []
      routes = self._adsb_service.get_routeset(entries)
      for entry in entries:
        try:
          callsign = entry.get('flight') or entry.get('r')
          callsign = callsign.strip()
          if not callsign:
            raise Exception("No callsign")
        except Exception:
          self.logger.warning(f'Entry {entry} does not have an identifier. Flight will not be logged.')
          continue

        stops = routes.get(callsign)
        origin, destination = '', ''
        if stops and self._flight_logic.validate_flight(flt=entry):
          try:
            route = self._flight_logic.analyze_route(flight=entry, stops=stops)
            if route:
              origin = route['origin']['airport_icao']
              destination = route['destination']['airport_icao']
          except Exception:
            self.logger.error(f'Error encountered analyzing route for flight {callsign}.', exc_info=True)
            origin, destination = '', ''
        item = _floats_to_decimal(entry)
        item['callsign'] = callsign
        item['origin'] = origin
        item['destination'] = destination
        item['timestamp'] = int(current_timestamp)
        item['timestamp_readable'] = datetime.fromtimestamp(current_timestamp / 1000).isoformat()
        item['expires_at'] = expires_at
        items.append(item)

      self._batch_write(items)

  def _batch_write(self, items: list[dict]):
    try:
      with self._table.batch_writer() as batch:
        for item in items:
          batch.put_item(Item=item)
      self.logger.info(f'{len(items)} record(s) written to {_DYNAMODB_TABLE_NAME}')
    except ClientError as e:
      if e.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
        self.logger.error(f'DynamoDB write throttled — {len(items)} entries dropped.')
      else:
        self.logger.error(f'Failed to write {len(items)} entries to DynamoDB.', exc_info=True)
    except Exception:
      self.logger.error(f'Failed to write {len(items)} entries to DynamoDB.', exc_info=True)


def _floats_to_decimal(obj):
  if isinstance(obj, float):
    return Decimal(str(obj))
  if isinstance(obj, dict):
    return {k: _floats_to_decimal(v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [_floats_to_decimal(v) for v in obj]
  return obj
