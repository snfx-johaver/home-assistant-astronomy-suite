"""Constants for Astronomy Space Suite."""

import json
from pathlib import Path

DOMAIN = "nasa_astronomy"

_MANIFEST_PATH = Path(__file__).parent / "manifest.json"


def _read_manifest_version() -> str:
    """Read the integration version from ``manifest.json``.

    ``manifest.json`` is the one version a release actually updates, so it is
    the single source for the ``sw_version`` every platform reports in its
    ``device_info``. Every platform registers against the same device, so a
    per-module literal meant one device carrying several conflicting version
    claims, with the displayed one decided by platform setup order.

    Read with the standard library rather than
    ``homeassistant.loader.async_get_integration``: ``device_info`` is built in
    synchronous entity constructors, which cannot await, so the Home Assistant
    route would force the version to be resolved in ``async_setup_entry`` and
    threaded through every platform's setup path and constructor signature.

    Falls back to ``"unknown"`` rather than raising: a missing or malformed
    manifest means Home Assistant would not have loaded the integration at all,
    and a cosmetic field is not worth failing the import over. The fallback
    cannot hide drift, because the regression test compares this value against
    the manifest it reads for itself.
    """
    try:
        with _MANIFEST_PATH.open(encoding="utf-8") as manifest:
            return str(json.load(manifest)["version"])
    except (OSError, ValueError, KeyError):
        return "unknown"


# Resolved once at import. Integration modules are imported off the event loop,
# so the single file read does not block it.
INTEGRATION_VERSION = _read_manifest_version()

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
