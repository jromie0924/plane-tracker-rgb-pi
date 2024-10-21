# TODO delete this config field
ZONE_HOME = {
    "tl_y": 42.039866, # Top-Left Latitude (deg) https://www.latlong.net/
    "tl_x": -87.826548, # Top-Left Longitude (deg)
    "br_y": 41.841827, # Bottom-Right Latitude (deg)
    "br_x": -87.456101 # Bottom-Right Longitude (deg)
}

DISTANCE_UNITS = "imperial"
CLOCK_FORMAT = "24hr" #use 12hr or 24hr
MIN_ALTITUDE = 2600 #feet
MAX_ALTITUDE = 50000  # feet
BRIGHTNESS = 100
BRIGHTNESS_NIGHT = 50
NIGHT_BRIGHTNESS = False #True for on False for off
NIGHT_START = "22:00"
NIGHT_END = "06:00"
GPIO_SLOWDOWN = 2 #depends what Pi you have I use 2 for Pi 3 and 1 for Pi Zero
JOURNEY_CODE_SELECTED = "xxx"
JOURNEY_BLANK_FILLER = " ? "
HAT_PWM_ENABLED = True
FORECAST_DAYS = 3 #today plus the next two days

CITY = "Chicago, IL"
RADIUS = 30 #miles (sort of - we use a box rather than a circle to represent the area we query for flights)

LIVE = False # True for live data, False for sandbox

API_TOKEN_KEY_NAME = 'api_key' if LIVE else 'api_key_sandbox'
AWS_ACCESS_KEY_ID_NAME = 'ACCESS_KEY_ID'
AWS_SECRET_ACCESS_KEY_NAME = 'SECRET_ACCESS_KEY'
AWS_REGION = 'us-east-1'

FLIGHTRADAR24_SECRET_NAME = 'flightradar24_api_key'
FLIGHTRADAR24_URL = 'fr24api.flightradar24.com'