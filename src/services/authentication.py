import boto3
import json
import os
import config
import logging
import threading
import time

from services.runtime import RuntimeService

_retries_allowed = 5

class AuthenticationService:
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(AuthenticationService, cls).__new__(cls)
        cls._instance.__init__()
      return cls._instance
  
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    self.error = False
    self.runtime_service = RuntimeService()
    retries = 1
    while retries < _retries_allowed:
      try:
        aws_access_key = self.runtime_service.aws_access_key_id
        aws_secret_key = self.runtime_service.aws_secret_access_key
        region = config.AWS_REGION
        rapidapi_secret_name = config.RAPIDAPI_KEY_NAME

        aws_secret_client = boto3.client('secretsmanager',
                                        aws_access_key_id=aws_access_key,
                                        aws_secret_access_key=aws_secret_key,
                                        region_name=region)
        
        response = aws_secret_client.get_secret_value(SecretId=rapidapi_secret_name)
        secret_value = json.loads(response['SecretString'])
        
        # rapidapi_token
        self._rapidapi_token = secret_value[config.RAPIDAPI_TOKEN_KEYNAME]
        break
      except Exception as e:
        self.logger.error(f"Error: {e}")
        # self.error = True
        self.logger.warning(f"Retrying to get secret value. Retry {retries}/{_retries_allowed}")
        retries += 1
        time.sleep(5)
        
        if retries == _retries_allowed:
          self.error = True
          self.logger.error(f"Failed to get secret value after {retries} retries")

  @property
  def rapidapi_token(self):
    if not self.error:
      return self._rapidapi_token
    else:
      return None