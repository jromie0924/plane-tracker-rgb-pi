from workers.animator import Animator
from setup import colours, fonts
# from RGBMatrixEmulator import graphics
from rgbmatrix import graphics
from config import DISTANCE_UNITS

# Attempt to load config data
try:
  from config import JOURNEY_CODE_SELECTED

except (ModuleNotFoundError, NameError, ImportError):
  # If there's no config data
  JOURNEY_CODE_SELECTED = "GLA"

try:
  from config import JOURNEY_BLANK_FILLER

except (ModuleNotFoundError, NameError, ImportError):
  # If there's no config data
  JOURNEY_BLANK_FILLER = " ? "

# Setup
JOURNEY_POSITION = (17, 0)
JOURNEY_HEIGHT = 10
JOURNEY_WIDTH = 48
JOURNEY_SPACING = 5
JOURNEY_FONT = fonts.regularplus
JOURNEY_FONT_SELECTED = fonts.regularplus_bold
ARROW_COLOUR = colours.GREY
DISTANCE_COLOUR = colours.TROPICAL_LIGHT_BLUE
DISTANCE_MEASURE = colours.TROPICAL_DARK_BLUE
DISTANCE_POSITION = (17, 16)
DISTANCE_WIDTH = 48
DISTANCE_FONT = fonts.extrasmall

# Element Positions
ARROW_POINT_POSITION = (41, 5)
ARROW_WIDTH = 3
ARROW_HEIGHT = 6


class JourneyScene(object):
  def __init__(self):
    super().__init__()

  @Animator.KeyFrame.add(0, scene_name="journey")
  def journey(self):
    # Guard against no data
    if len(self._data) == 0:
      return

    # Convert distance to either miles or kilometers based on UNITS configuration
    if DISTANCE_UNITS == "imperial":
      distance_units = "mi"
    elif DISTANCE_UNITS == "metric":
      distance_units = "KM"
    else:
      distance_units = "Units"

    # Format distance text
    distance_origin_text = f'{self._data[self._data_index]["distance_origin"]:.0f}{distance_units}'
    distance_destination_text = f'{self._data[self._data_index]["distance_destination"]:.0f}{distance_units}'

    # Grab Airport codes
    origin = self._data[self._data_index]["origin"]
    destination = self._data[self._data_index]["destination"]

    origin_color = self.determine_color(self._data[self._data_index]["distance_origin"])
    destination_color = self.determine_color(self._data[self._data_index]["distance_destination"])
    
    # Draw background with the chosen color
    self.draw_square(
      JOURNEY_POSITION[0],
      JOURNEY_POSITION[1],
      JOURNEY_POSITION[0] + JOURNEY_WIDTH - 1,
      JOURNEY_POSITION[1] + JOURNEY_HEIGHT - 1,
      colours.BLACK,
    )

    # Draw origin with the chosen color
    text_length = graphics.DrawText(
      self.canvas,
      JOURNEY_FONT_SELECTED if origin == JOURNEY_CODE_SELECTED else JOURNEY_FONT,
      JOURNEY_POSITION[0],
      JOURNEY_HEIGHT,
      origin_color,
      origin if origin else JOURNEY_BLANK_FILLER,
    )

    # Draw destination with the chosen color
    _ = graphics.DrawText(
      self.canvas,
      JOURNEY_FONT_SELECTED
      if destination == JOURNEY_CODE_SELECTED
      else JOURNEY_FONT,
      JOURNEY_POSITION[0] + text_length + JOURNEY_SPACING,
      JOURNEY_HEIGHT,
      destination_color,
      destination if destination else JOURNEY_BLANK_FILLER,
    )
    # Calculate the center of the available area
    center_x = (16 + 64) // 2

    # Calculate the width of each half
    half_width = (64 - 16) // 2

    # Calculate the width of the text using the font's character width (including space)
    font_character_width = 4
    distance_origin_text_width = len(distance_origin_text) * font_character_width
    distance_destination_text_width = len(distance_destination_text) * font_character_width

    # Calculate the adjusted positions for drawing the text
    distance_origin_x = center_x - half_width + (half_width - distance_origin_text_width) // 2
    distance_destination_x = center_x + (half_width - distance_destination_text_width) // 2
    
    # Iterate through each character in distance_origin_text
    distance_origin_text_length = 0
    for ch in distance_origin_text:
      ch_length = graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        distance_origin_x + distance_origin_text_length,
        DISTANCE_POSITION[1],  # Keep the same vertical position
        DISTANCE_COLOUR if ch.isnumeric() else DISTANCE_MEASURE,
        ch,
      )
      distance_origin_text_length += ch_length

    # Iterate through each character in distance_destination_text
    distance_destination_text_length = 0
    for ch in distance_destination_text:
      ch_length = graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        distance_destination_x + distance_destination_text_length,
        DISTANCE_POSITION[1],  # Keep the same vertical position
        DISTANCE_COLOUR if ch.isnumeric() else DISTANCE_MEASURE,
        ch,
      )
      distance_destination_text_length += ch_length

  @Animator.KeyFrame.add(0, scene_name="journey")
  def journey_arrow(self):
    # Guard against no data
    if len(self._data) == 0:
      return

    # Black area before arrow
    self.draw_square(
      ARROW_POINT_POSITION[0] - ARROW_WIDTH,
      ARROW_POINT_POSITION[1] - (ARROW_HEIGHT // 2),
      ARROW_POINT_POSITION[0],
      ARROW_POINT_POSITION[1] + (ARROW_HEIGHT // 2),
      colours.BLACK,
    )

    # Starting positions for filled in arrow
    x = ARROW_POINT_POSITION[0] - ARROW_WIDTH
    y1 = ARROW_POINT_POSITION[1] - (ARROW_HEIGHT // 2)
    y2 = ARROW_POINT_POSITION[1] + (ARROW_HEIGHT // 2)

    # Tip of arrow
    self.canvas.SetPixel(
      ARROW_POINT_POSITION[0],
      ARROW_POINT_POSITION[1],
      ARROW_COLOUR.red,
      ARROW_COLOUR.green,
      ARROW_COLOUR.blue,
    )

    # Draw using columns
    for col in range(0, ARROW_WIDTH):
      graphics.DrawLine(
        self.canvas,
        x,
        y1,
        x,
        y2,
        ARROW_COLOUR,
      )

      # Calculate next column's data
      x += 1
      y1 += 1
      y2 -= 1
  
  def determine_color(self, distance: int) -> colours:
    if distance >= 2000:
      return colours.XMAS_RED
    elif distance >= 1000:
      return colours.ORANGE
    elif distance >= 500:
      return colours.TROPICAL_ORANGE
    elif distance >= 200:
      return colours.YELLOW
    elif distance >= 100:
      return colours.GREEN
    else:
      return colours.TEAL
