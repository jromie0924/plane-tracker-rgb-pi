#!/usr/bin/python3
from display import Display
from models.runtimeModel import RuntimeModel
from services.runtime import RuntimeService
from logging.handlers import RotatingFileHandler

import config
import logging
import sys
import os
import csv

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
  
  # Rotating file handler
  # Will keep 2 files, each with a max size of 1MB
  # When the log file reaches 1MB, it will create a new log file
  # The oldest log file will be deleted
  file_handler = RotatingFileHandler(config.LOG_FILE, mode='a', maxBytes=1024*1024, backupCount=2)
  file_handler.setFormatter(formatter)
  
  # Add handlers to the logger
  logger.addHandler(file_handler)
  logger.addHandler(stream_handler)
  

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
  
  try:
    aws_secret_loc = sys.argv[1]
    runtime_service = RuntimeService()
    vars = setup(aws_secret_loc)
    runtime_service.set_runtime_vars(vars)
  except KeyError as e:
    logger.error(f"Error: {e}")
    sys.exit(1)
  
  # Run the program
  run_text = Display()
  run_text.run()