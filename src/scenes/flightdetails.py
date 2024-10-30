from utilities.animator import Animator
from setup import colours, fonts, screen

from RGBMatrixEmulator import graphics

# Setup
FLIGHT_NO_DISTANCE_FROM_TOP = 24
PLANE_DISTANCE_FROM_TOP = 31
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

    @Animator.KeyFrame.add(1, scene_name="flightdetails")
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

        self.draw_square(
            0,
            PLANE_DISTANCE_FROM_TOP - FLIGHT_NO_TEXT_HEIGHT,
            screen.WIDTH,
            PLANE_DISTANCE_FROM_TOP,
            colours.BLACK,
        )

        # Draw flight number if available
        flight_no_text_length = 0
        plane_details_text_length = 0
        callsign = self._data[self._data_index]["callsign"].replace('N/A', '')
        registration = self._data[self._data_index]['registration'].replace('N/A', '')
        plane_data = self._data[self._data_index]['plane']
        speed = self._data[self._data_index]['ground_speed']
        altitude = self._data[self._data_index]['altitude']
        direction = self._data[self._data_index]['direction']
        distance = self._data[self._data_index]['distance']
        distance_units = 'mi'

        plane_name_text = f'{plane_data} '
        distance_text = f'{distance:.2f}{distance_units} {direction} '
        altitude_text = f'{altitude}ft '
        speed_text = f'{speed}kts '

        if callsign or registration:
            # Remove icao from flight number
            # flight_no = callsign[len(self._data[self._data_index]["owner_icao"]):]
            if callsign:
                flight_no = callsign[len(self._data[self._data_index]["owner_icao"]):].strip() or callsign
            else:
                flight_no = registration

            # Add airline name if there is one
            if self._data[self._data_index]["airline"] != "":
                flight_no = f"{self._data[self._data_index]['airline']} {flight_no}"

            # full_text = f'{flight_no}\n{plane_name_text}{distance_text}'
            plane_details_text = f'{plane_name_text}{distance_text}{altitude_text}{speed_text}'

            for ch in flight_no:
                ch_length = graphics.DrawText(
                    self.canvas,
                    FLIGHT_NO_FONT,
                    self.flight_position + flight_no_text_length,
                    FLIGHT_NO_DISTANCE_FROM_TOP,
                    FLIGHT_NUMBER_NUMERIC_COLOUR if ch.isnumeric() else FLIGHT_NUMBER_ALPHA_COLOUR,
                    ch,
                )
                flight_no_text_length += ch_length
            
            # for ch in plane_details_text:
            plane_details_text_length = graphics.DrawText(
                self.canvas,
                FLIGHT_NO_FONT,
                self.flight_position + plane_details_text_length,
                PLANE_DISTANCE_FROM_TOP,
                colours.TROPICAL_ORANGE,
                plane_details_text,
            )
                # plane_details_text_length += ch_length

            text_length = max(plane_details_text_length, flight_no_text_length)

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
        if self.flight_position + text_length < 0:
            self.flight_position = screen.WIDTH
            # if len(self._data) > 1:
            #     self._data_index = (self._data_index + 1) % len(self._data)
            #     self._data_all_looped = (not self._data_index) or self._data_all_looped
            #     self.reset_scene()

    @Animator.KeyFrame.add(0, scene_name="flightdetails")
    def reset_scrolling(self):
        self.flight_position = screen.WIDTH