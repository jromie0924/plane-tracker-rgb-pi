import logging
import boto3
import threading
import config
import requests

from datetime import datetime
from services.runtime import RuntimeService

GET_IP_URL = "https://checkip.amazonaws.com"

class SsmService:
  _instance = None
  _lock = threading.Lock()

  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(SsmService, cls).__new__(cls)
        cls._instance.__init__()
      return cls._instance

  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self.logger = logging.getLogger(config.APP_NAME)
    self._runtime_service = RuntimeService()
    self._last_update = None
    self._initialized = True

  def _upload_to_ssm(self, ip: str):
    now = datetime.now().timestamp()
    window_seconds = config.ALLOWED_IP_UPDATE_FREQUENCY_MINUTES * 60
    if self._last_update and self._last_update + window_seconds >= now:
      self.logger.info(f"Last update was within the last {config.ALLOWED_IP_UPDATE_FREQUENCY_MINUTES} minutes. Skipping.")
      return
    try:
      ssm_client = boto3.client('ssm',
                            aws_access_key_id=self._runtime_service.aws_access_key_id,
                            aws_secret_access_key=self._runtime_service.aws_secret_access_key,
                            region_name=config.AWS_REGION)
      ssm_client.put_parameter(Name=config.SSM_API_ALLOWED_IP_NAME,
                              Value=ip,
                              Type='String',
                              Overwrite=True)
      self._last_update = now
      self.logger.info("Successfully updated allowed IP parameter.")
      self.logger.debug(f"New IP: {ip}")
    except Exception:
      self.logger.error("Failed to update allowed IP param", exc_info=True)

  def update_allowed_ip_secret(self):
    if not config.SSM_IP_UPDATE_ENABLED:
      self.logger.debug("SSM IP update disabled on this host. Skipping.")
      return
    self.logger.info("Updating allowed IP secret")
    response = requests.get(GET_IP_URL, timeout=2)
    response.raise_for_status()
    public_ip = response.text.strip()
    self._upload_to_ssm(public_ip)
