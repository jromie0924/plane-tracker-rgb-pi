#!/usr/bin/python3
from datetime import datetime
from display import Display
from models.runtimeModel import RuntimeModel
from services.runtime import RuntimeService
from setup.screen import IS_RASPBERRY_PI
from logging.handlers import TimedRotatingFileHandler

import config
import logging
import sys
import os
import csv
import faulthandler
import signal
import boto3
import watchtower

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(config.LOGGING_LEVEL)
  
  # Create log directory if it doesn't exist
  dir = os.path.dirname(config.LOG_FILE)
  os.makedirs(dir, exist_ok=True)
  
  # Log formatter
  formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

  # Stream handler (sys.stdout) for console output
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setFormatter(formatter)
  
  # Timed rotating file handler
  # Rotates log files daily at midnight
  # Will keep 30 days of log files
  # Older log files will be automatically deleted
  file_handler = TimedRotatingFileHandler(config.LOG_FILE, when='midnight', interval=1, backupCount=30)
  file_handler.setFormatter(formatter)
  
  # Add handlers to the logger
  logger.addHandler(file_handler)
  logger.addHandler(stream_handler)


def _add_cloudwatch_handler(access_key_id: str, secret_access_key: str, platform_is_pi: bool):
  logger = logging.getLogger(config.APP_NAME)
  log_group_name = f'plane-tracker-{"pi" if platform_is_pi else "emu"}'

  session = boto3.Session(
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name=config.AWS_REGION
  )

  stream_name = f'{"pi" if platform_is_pi else "emu"}-{datetime.now().strftime("%Y%m%dT%H%M%S")}'

  cw_handler = watchtower.CloudWatchLogHandler(
    log_group_name=log_group_name,
    log_stream_name=stream_name,
    boto3_client=session.client('logs'),
    create_log_group=True,
    log_group_retention_days=30,
  )
  cw_handler.setFormatter(logging.Formatter('[%(levelname)s] [%(module)s] %(message)s'))
  logger.addHandler(cw_handler)


def setup(aws_secret_loc: str):
  AWS_ACCESS_CREDS_FILENAME = 'flight_tracker_app_accessKeys.csv'

  ACCESS_KEY_ID_NAME = 'Access key ID'
  SECRET_ACCESS_KEY_NAME = 'Secret access key'

  runtime_model: RuntimeModel

  with open(f'{aws_secret_loc}/{AWS_ACCESS_CREDS_FILENAME}', mode='r', encoding='utf-8-sig') as file:
    csvFile = csv.DictReader(file)
    for line in csvFile:
      access_key_id = line[ACCESS_KEY_ID_NAME]
      secret_access_key = line[SECRET_ACCESS_KEY_NAME]
      runtime_model = RuntimeModel(aws_access_key_id=access_key_id,
                                   aws_secret_access_key=secret_access_key)
  return runtime_model

  
if __name__ == "__main__":
  # Set up logging for application
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  faulthandler.enable(all_threads=True)
  try:
    faulthandler.register(signal.SIGUSR1, all_threads=True)
  except Exception:
    pass
  
  try:
    aws_secret_loc = sys.argv[1]
    runtime_service = RuntimeService()
    vars = setup(aws_secret_loc)
    runtime_service.set_runtime_vars(vars)
    _add_cloudwatch_handler(vars._aws_access_key_id, vars._aws_secret_access_key, IS_RASPBERRY_PI)
  except KeyError as e:
    logger.error(f"Error: {e}")
    sys.exit(1)
  
  # Run the program
  run_text = Display()
  run_text.run()