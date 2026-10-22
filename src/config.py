from enum import Enum, unique
import logging

LOGGING_LEVEL: int = logging.INFO

@unique
class DataSource(Enum):
  API=1
  FEEDER=2


APP_NAME = "plane-tracker"
LOG_FILE = "logs/plane-tracker.log"
CLOUDWATCH_RETENTION_DAYS = 30

TRACKER_LOG_TTL_HOURS = 168 # 1 week
TRACKER_LOG_EMU_FLAG = False

DISTANCE_UNITS = "imperial"
CLOCK_FORMAT = "24hr" #use 12hr or 24hr

# Display scale factor for non-Pi systems (emulator)
# Options: 1 or 2 (default: 2)
# This controls the size of the display on non-Raspberry Pi systems
DISPLAY_SCALE_FACTOR = 2
MIN_ALTITUDE = 1000 #feet
MAX_ALTITUDE = 70000  # feet
BRIGHTNESS = 75
BRIGHTNESS_NIGHT = 50
NIGHT_BRIGHTNESS = True #True for on False for off
NIGHT_START = "20:30"
NIGHT_END = "07:00"
GPIO_SLOWDOWN = 4 # TODO - depends what Pi you have I use 2 for Pi 3 and 1 for Pi Zero
JOURNEY_CODE_SELECTED = "xxx"
JOURNEY_BLANK_FILLER = " ? "
HAT_PWM_ENABLED = False

ZIP_CODE = "60657"
COUNTRY = "USA"

# LOCATION_COORDINATES_OVERRIDE = [39.766098, -105.0772063] #[lat, lon]
LOCATION_COORDINATES_OVERRIDE = [] #[lat, lon]

LOCATION_CACHE_TIMEOUT = 30 # minutes
RADIUS = 30 # nautical miles
LOCATION_COORDINATES_DEFAULT = [41.8755616, -87.6244212] # Chicago, IL

DUPLICATION_AVOIDANCE_TTL = 3 # minutes
ROUTESET_LIMIT_SECONDS = 1 # second

RAPIDAPI_TOKEN_KEYNAME = 'rapidapi_key'
AWS_ACCESS_KEY_ID_NAME = 'ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY_NAME = 'SECRET_ACCESS_KEY'
AWS_REGION = 'us-east-2' # Ohio

'''
Data source used for retrieving ADSB data

API:    Use adsb.fi data. GitHub: https://github.com/adsbfi/opendata

FEEDER: Use local ADSB.im feeder data. Requires a local feeder on the same network
        Update _feeder_url accordingly to the appropriate local IP address.
'''
ADSB_DATA_SOURCE=DataSource.API

_adsb_fi_url = 'opendata.adsb.fi'
_feeder_url = '192.168.12.41:30152' # update to your local feeder IP address

match ADSB_DATA_SOURCE:
  case DataSource.API:
    ADSB_DATA_URL = _adsb_fi_url
  case DataSource.FEEDER:
    ADSB_DATA_URL = _feeder_url
  case _:
    ADSB_DATA_URL = ""

ADSB_PAYLOAD_ROOT_KEY = "aircraft" if ADSB_DATA_SOURCE == DataSource.FEEDER else "ac"

# Source of routes.csv.gz and airports.csv.gz (VRS standing data), used to build the local route database
ROUTE_DATA_URL = 'vrs-standing-data.adsb.lol'
ROUTE_DATA_REFRESH_DAYS = 1 # how often to check the route data for changes
ROUTE_DB_FILE = 'app_data/routes.db'

ADSB_USER_AGENT = f'{APP_NAME}/1.0 (+https://github.com/jromie0924/plane-tracker-rgb-pi)'

ROUTES_FILE = 'routes.csv.gz'
AIRPORTS_FILE = 'airports.csv.gz'

RAPIDAPI_KEY_NAME = 'plane_tracker_api_key'
RAPIDAPI_HOST = 'forward-reverse-geocoding.p.rapidapi.com'