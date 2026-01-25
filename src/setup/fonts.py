import os
from matrix_service import graphics
from setup import screen

# Fonts
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Determine font directory based on platform and scale factor
# Use scaled fonts for non-Pi systems (emulator)
if screen.IS_RASPBERRY_PI:
    FONT_DIR = f"{DIR_PATH}/../fonts"
    FONT_SUFFIX = ""
else:
    # Validate that scale factor has a corresponding font directory
    font_dir_candidate = f"{DIR_PATH}/../fonts/scaled_{screen.SCALE_FACTOR}x"
    if not os.path.exists(font_dir_candidate):
        print(f"Warning: Font directory {font_dir_candidate} does not exist. Falling back to scaled_3x.")
        FONT_DIR = f"{DIR_PATH}/../fonts/scaled_3x"
        FONT_SUFFIX = "_3x"
    else:
        FONT_DIR = font_dir_candidate
        FONT_SUFFIX = f"_{screen.SCALE_FACTOR}x"

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
    extrasmall.LoadFont(f"{FONT_DIR}/4x6{FONT_SUFFIX}.bdf")
    small.LoadFont(f"{FONT_DIR}/5x8{FONT_SUFFIX}.bdf")
    regular.LoadFont(f"{FONT_DIR}/6x13{FONT_SUFFIX}.bdf")
    regular_bold.LoadFont(f"{FONT_DIR}/6x13B{FONT_SUFFIX}.bdf")
    regularplus.LoadFont(f"{FONT_DIR}/7x13{FONT_SUFFIX}.bdf")
    regularplus_bold.LoadFont(f"{FONT_DIR}/7x13B{FONT_SUFFIX}.bdf")
    large.LoadFont(f"{FONT_DIR}/8x13{FONT_SUFFIX}.bdf")
    large_bold.LoadFont(f"{FONT_DIR}/8x13B{FONT_SUFFIX}.bdf")
