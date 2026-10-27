import boto3
import json
import os
import config
import logging
import threading
import time

from services.runtime import RuntimeService
from services.singleton import Singleton

_retries_allowed = 5

class AuthenticationService(Singleton):
  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True

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
        self.logger.warning(f"Retrying to get secret value. Retry {retries}/{_retries_allowed}")
        retries += 1
        time.sleep(5)
        if retries == _retries_allowed:
          self.error = True
          self.logger.error(f"Failed to get secret value after {retries} retries")
    
    if not self.error:
      self.logger.info(f"{self.__class__.__name__} successfully initialized.")
    else:
      self.logger.error(f"{self.__class__.__name__} initialized with errors.")

  @property
  def rapidapi_token(self):
    if not self.error:
      return self._rapidapi_token
    else:
      return None