import boto3
import json
import os
import config
import logging
import threading

from services.runtime import RuntimeService

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
    except Exception as e:
      self.logger.error(f"Error: {e}")
      self.error = True

  @property
  def rapidapi_token(self):
    if not self.error:
      return self._rapidapi_token
    else:
      return None