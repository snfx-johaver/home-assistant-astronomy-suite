"""Constants for NASA Astronomy Suite."""

DOMAIN = "nasa_astronomy"

CONF_UPDATE_INTERVAL = "update_interval"
CONF_ROCKET_API_KEY = "rocket_api_key"

BASE_URL = "https://api.nasa.gov"

APOD_URL = f"{BASE_URL}/planetary/apod"
NEOWS_URL = f"{BASE_URL}/neo/rest/v1/feed"
DONKI_CME_URL = f"{BASE_URL}/DONKI/CME"
DONKI_FLR_URL = f"{BASE_URL}/DONKI/FLR"
DONKI_GST_URL = f"{BASE_URL}/DONKI/GST"
EONET_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
MARS_WEATHER_URL = f"{BASE_URL}/insight_weather/"
TECHTRANSFER_URL = f"{BASE_URL}/techtransfer/patent/"

ROCKET_LAUNCH_URL = "https://fdo.rocketlaunch.live/json/launches/next/5"

# New no-auth sources
ISS_POSITION_URL = "http://api.open-notify.org/iss-now.json"
ISS_STREAM_URL = "https://www.youtube.com/watch?v=86YLFOog4GM"
EPIC_EARTH_URL = "https://epic.gsfc.nasa.gov/api/natural"
EPIC_IMAGE_BASE_URL = "https://epic.gsfc.nasa.gov/archive/natural"
GOES16_EARTH_URL = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/FD/GEOCOLOR/latest.jpg"
GOES18_EARTH_URL = "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/FD/GEOCOLOR/latest.jpg"
HIMAWARI8_EARTH_URL = "https://himawari8.nict.go.jp/img/D531106/latest.jpg"
SDO_SUN_URL = "https://sdo.gsfc.nasa.gov/assets/img/latest/latest_1024_0171.jpg"
SOHO_SUN_URL = "https://soho.nascom.nasa.gov/data/realtime/c3/1024/latest.jpg"
SWPC_KP_INDEX_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"

SENSOR_TYPES = {
    "apod": "Astronomy Picture of the Day",
    "neo_count": "Near Earth Objects Count",
    "neo_closest": "Closest NEO Today",
    "neo_fastest": "Fastest NEO Today",
    "neo_largest": "Largest NEO Today",
    "donki_cme": "Coronal Mass Ejections",
    "donki_flare": "Solar Flares",
    "donki_storm": "Geomagnetic Storms",
    "eonet_events": "Earth Events",
    "mars_weather": "Mars Weather",
    "techtransfer": "NASA Tech Transfer",
}

ATTR_NEO_LIST = "neo_list"
ATTR_APOD_TITLE = "title"
ATTR_APOD_EXPLANATION = "explanation"
ATTR_APOD_URL = "url"
ATTR_APOD_HDURL = "hdurl"
ATTR_APOD_DATE = "date"
ATTR_APOD_MEDIA_TYPE = "media_type"
