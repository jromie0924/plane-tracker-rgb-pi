from PIL import Image
import json
import os

from workers.animator import Animator
from setup import colours, screen

LOGO_SIZE = 16 * screen.SCALE_FACTOR
DEFAULT_IMAGE = "default"
LOGO_DIR = "logos" if screen.SCALE_FACTOR == 1 else f"logos_{screen.SCALE_FACTOR}x"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MISSING_LOGOS_DIR = os.path.join(REPO_ROOT, "missing_logos")
MISSING_LOGOS_FILE = os.path.join(MISSING_LOGOS_DIR, "missing_logos.json")


def _record_missing_logo(icao: str) -> None:
  os.makedirs(MISSING_LOGOS_DIR, exist_ok=True)

  missing_logos: dict[str, int] = {}
  if os.path.exists(MISSING_LOGOS_FILE):
    try:
      with open(MISSING_LOGOS_FILE, "r", encoding="utf-8") as file:
        missing_logos = json.load(file)
    except (json.JSONDecodeError, OSError):
      missing_logos = {}

  missing_logos[icao] = int(missing_logos.get(icao, 0)) + 1

  with open(MISSING_LOGOS_FILE, "w", encoding="utf-8") as file:
    json.dump(missing_logos, file, indent=2, sort_keys=True)

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
      _record_missing_logo(icao)
      image = Image.open(f"{LOGO_DIR}/{DEFAULT_IMAGE}.png")

    # Scale the logo according to the display scale factor
    # LOGO_SIZE = 16 * SCALE_FACTOR, so we scale from original size to target size
    # TODO: use this command to resize the new logos to 2x, 3x, and 4x multiples of 16 in zsh:
    # for img in input_images/*; do convert "$img" -resize 800x600 "output_images/$(basename "$img")"; done
    # if image.size != (LOGO_SIZE, LOGO_SIZE):
    #   image = image.resize((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
    
    self.matrix.SetImage(image.convert('RGB'))
