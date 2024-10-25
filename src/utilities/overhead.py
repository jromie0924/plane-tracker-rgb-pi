from service.adsbTracker import AdsbTrackerService
from service.airlineLookup import AirlineLookupService
from threading import Thread, Lock
from time import sleep
from typing import Optional, Tuple
from geopy.geocoders import Nominatim
from .geoUtils import GeoUtils

import threading
import math
import time
import geopy.distance as geodistance
import config

from requests.exceptions import ConnectionError
from urllib3.exceptions import NewConnectionError
from urllib3.exceptions import MaxRetryError

from config import LOCATION, RADIUS, MIN_ALTITUDE, MAX_ALTITUDE

RETRIES = 3
RATE_LIMIT_DELAY = 1
MAX_FLIGHT_LOOKUP = 5
EARTH_RADIUS_M = 3958.8  # Earth's radius in miles
BLANK_FIELDS = ["", "N/A", "NONE", "UNKNOWN"]
NW = 315 #degrees
SE = 135 #degrees

timelogs = []

# Calculate the zone where we want to see flight data.
ZONE = {}
try:
    geolocator = Nominatim(user_agent="plane_tracker")
    location = geolocator.geocode(LOCATION)
    distance_obj = geodistance.geodesic(miles=RADIUS)
    top_left = distance_obj.destination(point=location, bearing=NW)
    bottom_right = distance_obj.destination(point=location, bearing=SE)
    ZONE["tl_y"] = top_left.latitude
    ZONE["tl_x"] = top_left.longitude
    ZONE["br_y"] = bottom_right.latitude
    ZONE["br_x"] = bottom_right.longitude
    LOCATION_DEFAULT = [location.latitude, location.longitude]
except Exception:
    ZONE = {"tl_y": 41.9267684604688, "tl_x": -87.69301898128884, "br_y": 41.82431337321679, "br_x": -87.55593288861269}
    LOCATION_DEFAULT = [51.509865, -0.118092, EARTH_RADIUS_M]
    
def polar_to_cartesian(lat, long, alt):
        DEG2RAD = math.pi / 180
        return [
            alt * math.cos(DEG2RAD * lat) * math.sin(DEG2RAD * long),
            alt * math.sin(DEG2RAD * lat),
            alt * math.cos(DEG2RAD * lat) * math.cos(DEG2RAD * long),
        ]


def distance_from_flight_to_home(flight, home=LOCATION_DEFAULT):
    try:
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(flight.latitude), math.radians(flight.longitude)
        lat2, lon2 = math.radians(home[0]), math.radians(home[1])

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Haversine distance in miles using the defined Earth radius
        dist_miles = EARTH_RADIUS_M * c

        return dist_miles

    except AttributeError:
        # on error say it's far away
        return 1e6
               
def plane_bearing(flight, home=LOCATION_DEFAULT):
  # Convert latitude and longitude to radians
  lat1 = math.radians(home[0])
  long1 = math.radians(home[1])
  lat2 = math.radians(flight['lat'])
  long2 = math.radians(flight['lon'])

  # Calculate the bearing
  bearing = math.atan2(
      math.sin(long2 - long1) * math.cos(lat2),
      math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2 - long1)
  )

  # Convert the bearing to degrees
  bearing = math.degrees(bearing)

  # Make sure the bearing is positives
  return (bearing + 360) % 360
  
def degrees_to_cardinal(d):
    '''
    note: this is highly approximate...
    '''
    dirs = ["N", "NE",  "E",  "SE", 
            "S",  "SW",  "W",  "NW",]
    ix = int((d + 22.5)/45)
    return dirs[ix % 8]

# def distance_from_flight_to_origin(flight, origin_latitude, origin_longitude, origin_altitude):
#     if hasattr(flight, 'latitude') and hasattr(flight, 'longitude') and hasattr(flight, 'altitude'):
#         try:
#             # Convert latitude and longitude from degrees to radians
#             lat1, lon1 = math.radians(flight.latitude), math.radians(flight.longitude)
#             lat2, lon2 = math.radians(origin_latitude), math.radians(origin_longitude)

#             # Differences in coordinates
#             dlat = lat2 - lat1
#             dlon = lon2 - lon1

#             # Haversine formula
#             a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
#             c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

#             # Haversine distance in miles using the defined Earth radius
#             dist_miles = EARTH_RADIUS_M * c

#             return dist_miles
#         except Exception as e:
#             print("Error:", e)
#             return None
#     else:
#         print("Flight data is missing required attributes: latitude, longitude, or altitude")
#         return None

def distance_from_flight_to_location(flight, location_lat, location_lon, destination_altitude):
    try:
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(flight['lat']), math.radians(flight['lon'])
        lat2, lon2 = math.radians(location_lat), math.radians(location_lon)

        # Differences in coordinates
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Haversine distance in miles using the defined Earth radius
        dist_miles = EARTH_RADIUS_M * c

        return dist_miles
    except Exception as e:
        print("Error:", e)
        return None


class Overhead:
    def __init__(self):
        self._api = AdsbTrackerService()
        self._airline_lookup = AirlineLookupService()
        self._lock = Lock()
        self._data = []
        self._new_data = False
        self._processing = False
        self.geo = GeoUtils()

    def grab_data(self):
        Thread(target=self._grab_data).start()

    def _grab_data(self):
        # Mark data as old
        data = []

        # Grab flight details
        try:
            with self._lock:
                self._new_data = False
                self._processing = True
            print(f'thread {threading.current_thread().ident} obtained lock')

            flights = self._api.get_nearby_flight(self.geo.get_home_lat(), self.geo.get_home_lon(), config.RADIUS)

            flight = None
            for flt in flights:
                if flt['alt_baro'] <= config.MAX_ALTITUDE and flt['alt_baro'] >= config.MIN_ALTITUDE:
                    flight = flt
                    break

            # Sort flights by closest first
            # print(f'thread {threading.current_thread().ident} sorting flights')

            # flights = [f for f in flights if f['alt_geom'] <= config.MAX_ALTITUDE and f['alt_geom'] >= config.MIN_ALTITUDE]

            # print(f'thread {threading.current_thread().ident} finished sorting flights')
            # flights = sorted(flights, key=lambda f: distance_from_flight_to_home(f))

            # print(f'thread {threading.current_thread().ident} processing {len(flights)} flights')
            # for flight in flights[:MAX_FLIGHT_LOOKUP]:
            retries = RETRIES

            while retries:
                # Rate limit protection
                print(f'thread {threading.current_thread().ident} sleeping...')
                sleep(RATE_LIMIT_DELAY)
                print(f'thread {threading.current_thread().ident} waking up...')

                # Grab and store details
                try:
                    # details = self._api.get_flight_details(flight) # TODO: remove this line, and instead call the routeset endpoint
                    print(f'thread {threading.current_thread().ident} getting routeset for {flight["flight"]}')
                    details = self._api.get_routeset(flight['lat'], flight['lon'], flight['flight'])
                    print(f'thread {threading.current_thread().ident} finished getting routeset for flight {flight["flight"]}')

                    # Get plane type
                    try:
                        # plane = details["aircraft"]["model"]["code"]
                        plane = flight['t']
                    except (KeyError, TypeError):
                        plane = ""

                    # Tidy up what we pass along
                    plane = plane if not (plane.upper() in BLANK_FIELDS) else ""

                    # origin = (
                    #     flight.origin_airport_iata
                    #     if not (flight.origin_airport_iata.upper() in BLANK_FIELDS)
                    #     else ""
                    # )

                    # origin = details['_airports'][len(details['_airports']) - 2:][0]
                    airport_details = details['_airports'][len(details['_airports']) - 2:]

                    if len(airport_details):
                        origin = airport_details[0]
                        destination = airport_details[1]
                    else:
                        origin = {'iata': '', 'lat': 0, 'lon': 0, 'alt_feet': 0}
                        destination = {'iata': '', 'lat': 0, 'lon': 0, 'alt_feet': 0}

                    # destination = (
                    #     flight.destination_airport_iata
                    #     if not (flight.destination_airport_iata.upper() in BLANK_FIELDS)
                    #     else ""
                    # )
                    
                    # destination = details['_airports'][len(details['_airports']) - 2:][1]

                    # callsign = (
                    #     flight.callsign
                    #     if not (flight.callsign.upper() in BLANK_FIELDS)
                    #     else ""
                    # )
                    callsign: str = flight['flight']
                    if callsign.upper() in BLANK_FIELDS:
                        callsign = ''

                    # Get airline type
                    # try:
                    #     airline = details["airline"]["name"]
                    # except (KeyError, TypeError):
                    #     airline = ""

                    if (details['airline_code']):
                        airline = self._airline_lookup.lookup(details['airline_code'])
                    else:
                        airline = ''

                        
                    # Get departure and arrival times
                    try:
                        time_scheduled_departure = details["time"]["scheduled"]["departure"]
                        time_scheduled_arrival = details["time"]["scheduled"]["arrival"]
                        time_real_departure = details["time"]["real"]["departure"]
                        time_estimated_arrival = details["time"]["estimated"]["arrival"]
                    except (KeyError, TypeError):
                        time_scheduled_departure = None
                        time_scheduled_arrival = None
                        time_real_departure = None
                        time_estimated_arrival = None
                        
                    # Extract origin airport coordinates
                    # origin_latitude = None
                    # origin_longitude = None
                    # origin_altitude = None
                    # if details['airport']['origin'] is not None:
                    #     origin_latitude = details['airport']['origin']['position']['latitude']
                    #     origin_longitude = details['airport']['origin']['position']['longitude']
                    #     origin_altitude = details['airport']['origin']['position']['altitude']
                        #print("Origin Coordinates:", origin_latitude, origin_longitude, origin_altitude)

                    # Extract destination airport coordinates
                    # destination_latitude = None
                    # destination_longitude = None
                    # destination_altitude = None
                    # if details['airport']['destination'] is not None:
                    #     destination_latitude = details['airport']['destination']['position']['latitude']
                    #     destination_longitude = details['airport']['destination']['position']['longitude']
                    #     destination_altitude = details['airport']['destination']['position']['altitude']
                        #print("Destination Coordinates:", destination_latitude, destination_longitude, destination_altitude)

                    # Calculate distances using modified functions
                    distance_origin = 0
                    distance_destination = 0

                    # if origin_latitude is not None:
                    #     distance_origin = distance_from_flight_to_origin(
                    #         flight,
                    #         origin_latitude,
                    #         origin_longitude,
                    #         origin_altitude
                    #     )

                    distance_origin = distance_from_flight_to_location(flight,
                                                                        origin['lat'],
                                                                        origin['lon'],
                                                                        origin['alt_feet'])

                    # if destination_latitude is not None:
                    #     distance_destination = distance_from_flight_to_origin(
                    #         flight,
                    #         destination_latitude,
                    #         destination_longitude,
                    #         destination_altitude
                    #     )

                    distance_destination = distance_from_flight_to_location(flight,
                                                                                destination['lat'],
                                                                                destination['lon'],
                                                                                destination['alt_feet'])
                        

                    # Get owner icao
                    owner_icao = details['airline_code']

                    # owner_iata = flight.airline_iata or "N/A"
                    owner_iata = airline or 'N/A'

                    try:
                        vertical_speed = flight['baro_rate']
                    except KeyError:
                        try:
                            vertical_speed = flight['geom_rate']
                        except KeyError:
                            vertical_speed = 0
                        
                    data.append(
                        {
                            "airline": airline,
                            "plane": plane,
                            "origin": origin['iata'],
                            "owner_iata":owner_iata,
                            "owner_icao": owner_icao,
                            "destination": destination['iata'],
                            "vertical_speed": vertical_speed,
                            "callsign": callsign,
                            "distance_origin": distance_origin,
                            "distance_destination": distance_destination,
                            "distance": flight['dst'],
                            "direction": degrees_to_cardinal(plane_bearing(flight)),
                            "ground_speed": flight['gs'],
                            "altitude": flight['alt_geom']
                        }
                    )
                
                    break

                except (KeyError, AttributeError) as e:
                    retries -= 1

            with self._lock:
                self._new_data = True
                self._processing = False
                self._data = data

        except (ConnectionError, NewConnectionError, MaxRetryError):
            print("HERE")
            self._new_data = False
            self._processing = False

    @property
    def new_data(self):
        with self._lock:
            return self._new_data

    @property
    def processing(self):
        with self._lock:
            return self._processing

    @property
    def data(self):
        with self._lock:
            self._new_data = False
            return self._data

    @property
    def data_is_empty(self):
        return len(self._data) == 0


# Main function
if __name__ == "__main__":

    o = Overhead()
    o.grab_data()
    while not o.new_data:
        print("processing...")
        sleep(1)

    print(o.data)
