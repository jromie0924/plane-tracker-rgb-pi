import boto3
import json
import os
import config

class AuthenticationService:
  def __init__(self):
    self.error = False
    try:
      aws_access_key = os.environ.get(config.AWS_ACCESS_KEY_ID_NAME)
      aws_secret_key = os.environ.get(config.AWS_SECRET_ACCESS_KEY_NAME)
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
      print(f"Error: {e}")
      self.error = True

  def get_rapidapi_token(self):
    if not self.error:
      return self._rapidapi_token
    else:
      return None