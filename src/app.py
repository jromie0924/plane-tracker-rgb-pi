#!/usr/bin/python3
from display import Display
from setup.setup import setup
from logging.handlers import RotatingFileHandler

import config
import logging
import sys
import os

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(logging.INFO)
  
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

if __name__ == "__main__":
  # Set up logging for application
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  # Set up runtime environment vars
  setup()
  
  # Run the program
  run_text = Display()
  run_text.run()
