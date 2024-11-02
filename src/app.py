#!/usr/bin/python3
from display import Display
from setup.setup import setup

import config
import logging
import sys

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(logging.INFO)
  formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s]:[%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  
  stream_handler = logging.StreamHandler(sys.stdout)
  
  if not config.IS_RASPBERRY_PI:
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
  
  
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)

if __name__ == "__main__":
  # Create a display and
  # start its animation
  
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  setup()
  run_text = Display()
  run_text.run()
