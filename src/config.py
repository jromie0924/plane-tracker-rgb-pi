# TODO delete this config field
ZONE_HOME = {
    "tl_y": 42.039866, # Top-Left Latitude (deg) https://www.latlong.net/
    "tl_x": -87.826548, # Top-Left Longitude (deg)
    "br_y": 41.841827, # Bottom-Right Latitude (deg)
    "br_x": -87.456101 # Bottom-Right Longitude (deg)
}

DISTANCE_UNITS = "imperial"
CLOCK_FORMAT = "24hr" #use 12hr or 24hr
MIN_ALTITUDE = 2500 #feet
MAX_ALTITUDE = 50000  # feet
BRIGHTNESS = 100
BRIGHTNESS_NIGHT = 50
NIGHT_BRIGHTNESS = False #True for on False for off
NIGHT_START = "22:00"
NIGHT_END = "06:00"
GPIO_SLOWDOWN = 4 # TODO - depends what Pi you have I use 2 for Pi 3 and 1 for Pi Zero
JOURNEY_CODE_SELECTED = "xxx"
JOURNEY_BLANK_FILLER = " ? "
HAT_PWM_ENABLED = True
FORECAST_DAYS = 3 # today plus the next two days

LOCATION = "Chicago, IL 60657"
RADIUS = 30 # nautical miles

DUPLICATION_AVOIDANCE_TTL = 5 # minutes

LIVE = False # True for live data, False for sandbox

# TODO: Once the adsb.lol API requires a key, update the secret with the key, and update this field accordingly.
API_TOKEN_KEY_NAME = 'api_key' if LIVE else 'api_key_sandbox'
AWS_ACCESS_KEY_ID_NAME = 'ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY_NAME = 'SECRET_ACCESS_KEY'
AWS_REGION = 'us-east-2' # Ohio

ADSB_API_SECRET_NAME = '' # TODO: update this value to include the secret name from AWS secrets.
ADSB_LOL_URL = 'api.adsb.lol'