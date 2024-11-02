#!/usr/bin/python3
from display import Display
from setup.setup import setup

import config
import logging
import sys

def _init_logger():
  logger = logging.getLogger(config.APP_NAME)
  logger.setLevel(logging.INFO)
  
  handler = logging.StreamHandler(sys.stdout)
  
  formatter = logging.Formatter('[%(asctime)s]:[%(levelname)s]:[%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  handler.setFormatter(formatter)
  logger.addHandler(handler)

if __name__ == "__main__":
  # Create a display and
  # start its animation
  
  _init_logger()
  logger = logging.getLogger(config.APP_NAME)
  logger.info("Starting display")

  setup()
  run_text = Display()
  run_text.run()
