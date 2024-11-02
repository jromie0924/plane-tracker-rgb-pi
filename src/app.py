#!/usr/bin/python3
from display import Display
from setup.setup import setup

import config
import logging
import sys

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(logging.INFO)
  
  stream_handler = logging.StreamHandler(sys.stdout)
  file_handler = logging.FileHandler(config.LOG_FILE)
  
  
  formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s]:[%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)
  logger.addHandler(file_handler)

if __name__ == "__main__":
  # Create a display and
  # start its animation
  
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  setup()
  run_text = Display()
  run_text.run()
