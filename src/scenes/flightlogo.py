from PIL import Image
import os

from workers.animator import Animator
from setup import colours, screen

LOGO_SIZE = 16 * screen.SCALE_FACTOR
DEFAULT_IMAGE = "default"
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

    # Scale the logo according to the display scale factor
    # LOGO_SIZE = 16 * SCALE_FACTOR, so we scale from original size to target size
    if image.size != (LOGO_SIZE, LOGO_SIZE):
      image = image.resize((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    
    self.matrix.SetImage(image.convert('RGB'))
