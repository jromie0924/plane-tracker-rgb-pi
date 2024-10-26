from utilities.animator import Animator
from setup import colours, fonts, screen

from RGBMatrixEmulator import graphics

# Setup
FLIGHT_NO_DISTANCE_FROM_TOP = 24
FLIGHT_NO_TEXT_HEIGHT = 8  # based on font size
FLIGHT_NO_FONT = fonts.small

FLIGHT_NUMBER_ALPHA_COLOUR = colours.TROPICAL_GREEN
FLIGHT_NUMBER_NUMERIC_COLOUR = colours.TROPICAL_YELLOW

DATA_INDEX_POSITION = (52, 24)
DATA_INDEX_TEXT_HEIGHT = 7
DATA_INDEX_FONT = fonts.extrasmall

DATA_INDEX_COLOUR = colours.GREY


class FlightDetailsScene(object):
    def __init__(self):
        super().__init__()
        self.flight_position = screen.WIDTH
        self._data_all_looped = False
        self.flight_details_length = 0

    @Animator.KeyFrame.add(1)
    def flight_details(self, count):

        # Guard against no data
        if len(self._data) == 0:
            return

        # Clear the whole area
        self.draw_square(
            0,
            FLIGHT_NO_DISTANCE_FROM_TOP - FLIGHT_NO_TEXT_HEIGHT,
            screen.WIDTH,
            FLIGHT_NO_DISTANCE_FROM_TOP,
            colours.BLACK,
        )

        # Draw flight number if available
        flight_no_text_length = 0
        callsign = self._data[self._data_index]["callsign"]
        plane_data = self._data[self._data_index]['plane']
        direction = self._data[self._data_index]['direction']
        distance = self._data[self._data_index]['distance']
        distance_units = 'mi'

        plane_name_text = f'{plane_data} '
        distance_text = f'{distance:.2f}{distance_units} {direction} '

        if callsign and callsign != "N/A":
            # Remove icao from flight number
            flight_no = callsign[len(self._data[self._data_index]["owner_icao"]):]
            
            # Add airline name if there is one
            if self._data[self._data_index]["airline"] != "":
                flight_no = f"{self._data[self._data_index]['airline']} {flight_no}"

            full_text = f'{flight_no}\n{plane_name_text}{distance_text}'

            for ch in full_text:
                ch_length = graphics.DrawText(
                    self.canvas,
                    FLIGHT_NO_FONT,
                    self.flight_position + flight_no_text_length,
                    FLIGHT_NO_DISTANCE_FROM_TOP,
                    FLIGHT_NUMBER_NUMERIC_COLOUR if ch.isnumeric() else FLIGHT_NUMBER_ALPHA_COLOUR,
                    ch,
                )
                flight_no_text_length += ch_length

        # Draw bar
        if len(self._data) > 1:
            # Clear are where N of M might have been
            self.draw_square(
                DATA_INDEX_POSITION[1],
                FLIGHT_NO_DISTANCE_FROM_TOP - FLIGHT_NO_TEXT_HEIGHT,
                screen.WIDTH,
                FLIGHT_NO_DISTANCE_FROM_TOP,
                colours.BLACK,
            )

            # Draw text
            # text_length = graphics.DrawText(
            #     self.canvas,
            #     fonts.extrasmall,
            #     DATA_INDEX_POSITION[0],
            #     DATA_INDEX_POSITION[1],
            #     DATA_INDEX_COLOUR,
            #     f"{self._data_index + 1}/{len(self._data)}",
            # )

            # Count the whole line length
            # flight_no_text_length += text_length
        self.flight_details_length = flight_no_text_length

        # Handle scrolling
        self.flight_position -= 1
        if self.flight_position + flight_no_text_length < 0:
            self.flight_position = screen.WIDTH
            # if len(self._data) > 1:
            #     self._data_index = (self._data_index + 1) % len(self._data)
            #     self._data_all_looped = (not self._data_index) or self._data_all_looped
            #     self.reset_scene()

    @Animator.KeyFrame.add(0)
    def reset_scrolling(self):
        self.flight_position = screen.WIDTH