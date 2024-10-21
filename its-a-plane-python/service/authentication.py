import boto3
import os
import config

class AuthenticationService:
  def __init__(self):
    aws_access_key = os.environ.get(config.AWS_ACCESS_KEY_ID_NAME)
    aws_secret_key = os.environ.get(config.AWS_SECRET_ACCESS_KEY_NAME)
    region = config.AWS_REGION
    flightradar24_secret_name = config.FLIGHTRADAR24_SECRET_NAME

    aws_secret_client = boto3.client('secretsmanager',
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_client=aws_secret_key,
                                     region=region)
    
    response = aws_secret_client.get_secret_value(SecretId=flightradar24_secret_name)
    secret_value = response['SecretString']

    # FlightRadar24 api token
    self.flightradar24_token = secret_value[config.API_TOKEN_KEY_NAME]