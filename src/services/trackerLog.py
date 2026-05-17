import threading
import config
import logging
import boto3

from decimal import Decimal
from datetime import datetime
from utils.timeUtils import TimeUtils
from services.runtime import RuntimeService
from setup.screen import IS_RASPBERRY_PI

_DYNAMODB_TABLE_NAME = 'tracker_log' if IS_RASPBERRY_PI else 'tracker_log_emu'


class TrackerLog:
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(TrackerLog, cls).__new__(cls)
      return cls._instance

  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    self.logger = logging.getLogger(config.APP_NAME)
    runtime = RuntimeService()
    self._table = boto3.resource(
      'dynamodb',
      aws_access_key_id=runtime.aws_access_key_id,
      aws_secret_access_key=runtime.aws_secret_access_key,
      region_name=config.AWS_REGION
    ).Table(_DYNAMODB_TABLE_NAME)

  def update_log(self, entries: list[dict]):
    current_timestamp = TimeUtils.current_time_milli()
    expires_at = int(current_timestamp / 1000) + config.TRACKER_LOG_TTL_HOURS * 3600

    items = []
    for entry in entries:
      try:
        callsign = entry.get('flight') or entry.get('r')
        callsign = callsign.strip()
      except AttributeError:
        self.logger.warning(f'Entry {entry} does not have an identifier. Flight will not be logged.')
        continue

      item = _floats_to_decimal(entry)
      item['callsign'] = callsign
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
    except Exception:
      self.logger.error('Failed to write entries to DynamoDB.', exc_info=True)


def _floats_to_decimal(obj):
  if isinstance(obj, float):
    return Decimal(str(obj))
  if isinstance(obj, dict):
    return {k: _floats_to_decimal(v) for k, v in obj.items()}
  if isinstance(obj, list):
    return [_floats_to_decimal(v) for v in obj]
  return obj
