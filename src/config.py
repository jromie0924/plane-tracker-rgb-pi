import logging

LOGGING_LEVEL: int = logging.INFO

APP_NAME = "plane-tracker"
LOG_FILE = "logs/plane-tracker.log"

DISTANCE_UNITS = "imperial"
CLOCK_FORMAT = "24hr" #use 12hr or 24hr

# Display scale factor for non-Pi systems (emulator)
# Options: 1, 2, or 3 (default: 1)
# This controls the size of the display on non-Raspberry Pi systems
DISPLAY_SCALE_FACTOR = 2
MIN_ALTITUDE = 1000 #feet
MAX_ALTITUDE = 55000  # feet
BRIGHTNESS = 100
BRIGHTNESS_NIGHT = 50
NIGHT_BRIGHTNESS = False #True for on False for off
NIGHT_START = "22:00"
NIGHT_END = "06:00"
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

# TODO: Once the adsb.lol API requires a key, update the secret with the key, and update this field accordingly.
RAPIDAPI_TOKEN_KEYNAME = 'rapidapi_key'
AWS_ACCESS_KEY_ID_NAME = 'ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY_NAME = 'SECRET_ACCESS_KEY'
AWS_REGION = 'us-east-2' # Ohio

ADSB_API_SECRET_NAME = '' # TODO: update this value to include the secret name from AWS secrets.
ADSB_LOL_URL = 'api.adsb.lol'

RAPIDAPI_KEY_NAME = 'plane_tracker_api_key'
RAPIDAPI_HOST = 'forward-reverse-geocoding.p.rapidapi.com'