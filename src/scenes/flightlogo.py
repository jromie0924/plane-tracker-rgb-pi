from PIL import Image
import os

from workers.animator import Animator
from setup import colours, screen

LOGO_SIZE = 16 * screen.SCALE_FACTOR
DEFAULT_IMAGE = "default"

# Determine logo directory based on scale factor
# Use higher resolution logos for larger displays
if screen.SCALE_FACTOR >= 3:
    LOGO_DIR = "logos_48x48"
    # Validate directory exists, fallback to 16x16 logos if not
    if not os.path.exists(LOGO_DIR):
        print(f"Warning: {LOGO_DIR} directory not found. Using standard 16x16 logos.")
        LOGO_DIR = "logos"
else:
    LOGO_DIR = "logos"

class FlightLogoScene:
  @Animator.KeyFrame.add(0, scene_name="flightlogo")
  def logo_details(self):

    # Guard against no data
    if len(self._data) == 0:
      return

    # Clear the whole area
    self.draw_square(
      0,
      0,
      LOGO_SIZE,
      LOGO_SIZE,
      colours.BLACK,
    )

    icao = self._data[self._data_index]["owner_icao"]
    if icao in ("", "N/A"):
      icao = DEFAULT_IMAGE

    # Open the file
    try:
      image = Image.open(f"{LOGO_DIR}/{icao}.png")
    except FileNotFoundError:
      image = Image.open(f"{LOGO_DIR}/{DEFAULT_IMAGE}.png")

    # Make image fit our screen.
    image.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    self.matrix.SetImage(image.convert('RGB'))
