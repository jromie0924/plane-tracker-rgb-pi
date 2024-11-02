#!/usr/bin/python3
from display import Display
from setup.setup import setup
from logging.handlers import RotatingFileHandler

import config
import logging
import sys

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(logging.INFO)
  formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  
  stream_handler = logging.StreamHandler(sys.stdout)
  
  # Supports logging up to 5 64MB files.
  file_handler = RotatingFileHandler(config.LOG_FILE, mode='a', maxBytes=64*1024*1024, backupCount=5)
  file_handler.setFormatter(formatter)
  logger.addHandler(file_handler)
  
  
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)

if __name__ == "__main__":
  # Set up logging for application
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  # Set up runtime environment vars
  setup()
  
  # Run the tracker
  run_text = Display()
  run_text.run()
