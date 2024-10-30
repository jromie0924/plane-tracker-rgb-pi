import os
import csv
import config

def setup():
  AWS_SECRETS_ENV_VAR = 'AWS_SECRET'
  AWS_ACCESS_CREDS_FILENAME = 'flight_tracker_app_accessKeys.csv'

  ACCESS_KEY_ID_NAME = 'Access key ID'
  SECRET_ACCESS_KEY_NAME = 'Secret access key'

  aws_secret_loc = os.environ.get(AWS_SECRETS_ENV_VAR)

  with open(f'{aws_secret_loc}/{AWS_ACCESS_CREDS_FILENAME}', mode='r', encoding='utf-8-sig') as file:
    csvFile = csv.DictReader(file)
    for line in csvFile:
      access_key_id = line[ACCESS_KEY_ID_NAME]
      secret_access_key = line[SECRET_ACCESS_KEY_NAME]
      os.environ[config.AWS_ACCESS_KEY_ID_NAME] = access_key_id
      os.environ[config.AWS_SECRET_ACCESS_KEY_NAME] = secret_access_key