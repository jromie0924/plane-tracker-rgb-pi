APP_NAME = "plane-tracker"
LOG_FILE = "plane-tracker.log"

IS_RASPBERRY_PI = True

DISTANCE_UNITS = "imperial"
CLOCK_FORMAT = "24hr" #use 12hr or 24hr
MIN_ALTITUDE = 2500 #feet
MAX_ALTITUDE = 100000  # feet
BRIGHTNESS = 100
BRIGHTNESS_NIGHT = 50
NIGHT_BRIGHTNESS = False #True for on False for off
NIGHT_START = "22:00"
NIGHT_END = "06:00"
GPIO_SLOWDOWN = 4 # TODO - depends what Pi you have I use 2 for Pi 3 and 1 for Pi Zero
JOURNEY_CODE_SELECTED = "xxx"
JOURNEY_BLANK_FILLER = " ? "
HAT_PWM_ENABLED = False

STREET = ''
CITY = "Chicago"
ZIP_CODE = "60657"
STATE = "IL"
COUNTRY = "USA"

LOCATION_CACHE_TIMEOUT = 30 # minutes
RADIUS = 30 # nautical miles
LOCATION_COORDINATES_DEFAULT = [41.8755616, -87.6244212] # Chicago, IL

DUPLICATION_AVOIDANCE_TTL = 5 # minutes


# TODO: Once the adsb.lol API requires a key, update the secret with the key, and update this field accordingly.
RAPIDAPI_TOKEN_KEYNAME = 'rapidapi_key'
AWS_ACCESS_KEY_ID_NAME = 'ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY_NAME = 'SECRET_ACCESS_KEY'
AWS_REGION = 'us-east-2' # Ohio

ADSB_API_SECRET_NAME = '' # TODO: update this value to include the secret name from AWS secrets.
ADSB_LOL_URL = 'api.adsb.lol'

RAPIDAPI_KEY_NAME = 'plane_tracker_api_key'
RAPIDAPI_HOST = 'forward-reverse-geocoding.p.rapidapi.com'