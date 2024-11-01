#!/usr/bin/python3
from display import Display
from setup.setup import setup


if __name__ == "__main__":
  # Create a display and
  # start its animation

  setup()
  run_text = Display()
  run_text.run()
