from workers.animator import Animator
from setup import colours, fonts, screen
from services.matrix_service import graphics
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
JOURNEY_POSITION = (17 * screen.SCALE_FACTOR, 0)
JOURNEY_HEIGHT = 10 * screen.SCALE_FACTOR
JOURNEY_WIDTH = 48 * screen.SCALE_FACTOR
JOURNEY_SPACING = 5 * screen.SCALE_FACTOR
JOURNEY_FONT = fonts.regularplus
JOURNEY_FONT_SELECTED = fonts.regularplus_bold
ARROW_COLOUR = colours.GREY
DISTANCE_COLOUR = colours.TROPICAL_LIGHT_BLUE
DISTANCE_MEASURE = colours.TROPICAL_DARK_BLUE
DISTANCE_POSITION = (17 * screen.SCALE_FACTOR, 16 * screen.SCALE_FACTOR)
DISTANCE_WIDTH = 48 * screen.SCALE_FACTOR
DISTANCE_FONT = fonts.extrasmall

# Element Positions
ARROW_POINT_POSITION = (41 * screen.SCALE_FACTOR, 5 * screen.SCALE_FACTOR)
ARROW_WIDTH = 3 * screen.SCALE_FACTOR
ARROW_HEIGHT = 6 * screen.SCALE_FACTOR


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
    # Calculate the available width for distance display
    # Left side is for origin, right side is for destination
    left_start_x = JOURNEY_POSITION[0]
    left_end_x = JOURNEY_POSITION[0] + JOURNEY_WIDTH // 2
    right_start_x = JOURNEY_POSITION[0] + JOURNEY_WIDTH // 2
    right_end_x = min(JOURNEY_POSITION[0] + JOURNEY_WIDTH, screen.WIDTH * screen.SCALE_FACTOR)
    
    # Calculate actual text widths by measuring
    distance_origin_text_length = 0
    origin_x_positions = []
    for ch in distance_origin_text:
      ch_length = graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        0,  # Dummy position for measurement
        0,  # Dummy position
        DISTANCE_COLOUR,
        ch,
      )
      origin_x_positions.append(ch_length)
      distance_origin_text_length += ch_length
    
    distance_destination_text_length = 0
    destination_x_positions = []
    for ch in distance_destination_text:
      ch_length = graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        0,  # Dummy position for measurement
        0,  # Dummy position
        DISTANCE_COLOUR,
        ch,
      )
      destination_x_positions.append(ch_length)
      distance_destination_text_length += ch_length
    
    # Center the text within available space
    left_available_width = left_end_x - left_start_x
    right_available_width = right_end_x - right_start_x
    
    distance_origin_x = left_start_x + max(0, (left_available_width - distance_origin_text_length) // 2)
    distance_destination_x = right_start_x + max(0, (right_available_width - distance_destination_text_length) // 2)
    
    # Clamp to ensure text doesn't exceed boundaries
    distance_origin_x = min(distance_origin_x, left_end_x - distance_origin_text_length)
    distance_destination_x = min(distance_destination_x, right_end_x - distance_destination_text_length)
    
    # Draw distance_origin_text
    distance_origin_current_x = distance_origin_x
    for i, ch in enumerate(distance_origin_text):
      graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        distance_origin_current_x,
        DISTANCE_POSITION[1],
        DISTANCE_COLOUR if ch.isnumeric() else DISTANCE_MEASURE,
        ch,
      )
      distance_origin_current_x += origin_x_positions[i]

    # Draw distance_destination_text
    distance_destination_current_x = distance_destination_x
    for i, ch in enumerate(distance_destination_text):
      graphics.DrawText(
        self.canvas,
        DISTANCE_FONT,
        distance_destination_current_x,
        DISTANCE_POSITION[1],
        DISTANCE_COLOUR if ch.isnumeric() else DISTANCE_MEASURE,
        ch,
      )
      distance_destination_current_x += destination_x_positions[i]

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
