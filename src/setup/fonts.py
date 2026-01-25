import os
from matrix_service import graphics
from setup import screen

# Fonts
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Determine font directory based on platform
# Use scaled fonts for non-Pi systems (emulator)
if screen.IS_RASPBERRY_PI:
    FONT_DIR = f"{DIR_PATH}/../fonts"
else:
    FONT_DIR = f"{DIR_PATH}/../fonts/scaled"

extrasmall = graphics.Font()
small = graphics.Font()
regular = graphics.Font()
regular_bold = graphics.Font()
regularplus = graphics.Font()
regularplus_bold = graphics.Font()
large = graphics.Font()
large_bold = graphics.Font()

# Load fonts with appropriate scaling
if screen.IS_RASPBERRY_PI:
    extrasmall.LoadFont(f"{FONT_DIR}/4x6.bdf")
    small.LoadFont(f"{FONT_DIR}/5x8.bdf")
    regular.LoadFont(f"{FONT_DIR}/6x13.bdf")
    regular_bold.LoadFont(f"{FONT_DIR}/6x13B.bdf")
    regularplus.LoadFont(f"{FONT_DIR}/7x13.bdf")
    regularplus_bold.LoadFont(f"{FONT_DIR}/7x13B.bdf")
    large.LoadFont(f"{FONT_DIR}/8x13.bdf")
    large_bold.LoadFont(f"{FONT_DIR}/8x13B.bdf")
else:
    extrasmall.LoadFont(f"{FONT_DIR}/4x6_4x.bdf")
    small.LoadFont(f"{FONT_DIR}/5x8_4x.bdf")
    regular.LoadFont(f"{FONT_DIR}/6x13_4x.bdf")
    regular_bold.LoadFont(f"{FONT_DIR}/6x13B_4x.bdf")
    regularplus.LoadFont(f"{FONT_DIR}/7x13_4x.bdf")
    regularplus_bold.LoadFont(f"{FONT_DIR}/7x13B_4x.bdf")
    large.LoadFont(f"{FONT_DIR}/8x13_4x.bdf")
    large_bold.LoadFont(f"{FONT_DIR}/8x13B_4x.bdf")
