"""Optional bounded satellite passes using existing CelesTrak OMM and SGP4."""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone

import astronomy
from sgp4 import omm
from sgp4.api import Satrec, jday
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .coordinator import NasaDataCoordinator
from .providers.eclipses import _time
from .providers.forecast import ForecastRequest, number, stamp
from .providers.sky_intelligence import horizon_at

_LOGGER = logging.getLogger(__name__)
MAX_SATELLITES = 8
MAX_PASSES = 6
MAX_TRAIL = 60
CATALOG = {25544: "ISS", 20580: "Hubble", 48274: "Tiangong", 28654: "NOAA 18", 33591: "NOAA 19", 43013: "NOAA 20", 25994: "Terra", 27424: "Aqua"}


def selected_ids(values):
    if not isinstance(values, list) or len(values) > MAX_SATELLITES:
        raise ValueError("Select at most eight satellites")
    ids = []
    for value in values:
        ident = int(number(value, 1, 999999))
        if ident != float(value):
            raise ValueError("NORAD IDs must be integers")
        if ident not in ids:
            ids.append(ident)
    return ids


def parse_elements(ident):
    def parse(payload):
        if not isinstance(payload, list) or len(payload) != 1:
            raise ValueError("Missing orbital elements")
        fields = payload[0]
        if int(fields["NORAD_CAT_ID"]) != ident:
            raise ValueError("Wrong satellite returned")
        epoch = stamp(fields["EPOCH"])
        now = datetime.now(timezone.utc)
        if not -timedelta(hours=24) <= now - epoch <= timedelta(days=7):
            raise ValueError("Orbital elements outside age limit")
        for key, limits in (
            ("MEAN_MOTION", (.001, 20)), ("ECCENTRICITY", (0, .999999)),
            ("INCLINATION", (0, 180)), ("RA_OF_ASC_NODE", (0, 360)),
            ("ARG_OF_PERICENTER", (0, 360)), ("MEAN_ANOMALY", (0, 360)),
            ("BSTAR", (-10000, 10000)), ("MEAN_MOTION_DOT", (-10000, 10000)),
            ("MEAN_MOTION_DDOT", (-10000, 10000)),
        ):
            number(fields[key], *limits)
        satellite = Satrec()
        omm.initialize(satellite, fields)
        return dict(fields)
    return parse


def sidereal(jd):
    centuries = (jd - 2451545) / 36525
    return math.radians(((67310.54841 + (876600 * 3600 + 8640184.812866) * centuries + .093104 * centuries**2 - .0000062 * centuries**3) / 240) % 360)


def position(satellite, observer, at):
    jd, fraction = jday(at.year, at.month, at.day, at.hour, at.minute, at.second + at.microsecond / 1e6)
    error, vector, _ = satellite.sgp4(jd, fraction)
    if error or any(not math.isfinite(value) for value in vector):
        raise ValueError(f"SGP4 propagation error {error}")
    theta = sidereal(jd + fraction)
    x, y, z = vector
    ecef = (math.cos(theta) * x + math.sin(theta) * y, -math.sin(theta) * x + math.cos(theta) * y, z)
    lat, lon = math.radians(observer.latitude), math.radians(observer.longitude)
    normal = 6378.137 / math.sqrt(1 - .00669437999014 * math.sin(lat)**2)
    height = observer.height / 1000
    origin = ((normal + height) * math.cos(lat) * math.cos(lon), (normal + height) * math.cos(lat) * math.sin(lon), (normal * (1 - .00669437999014) + height) * math.sin(lat))
    dx, dy, dz = (ecef[i] - origin[i] for i in range(3))
    east = -math.sin(lon) * dx + math.cos(lon) * dy
    north = -math.sin(lat) * math.cos(lon) * dx - math.sin(lat) * math.sin(lon) * dy + math.cos(lat) * dz
    up = math.cos(lat) * math.cos(lon) * dx + math.cos(lat) * math.sin(lon) * dy + math.sin(lat) * dz
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    latitude, longitude = NasaDataCoordinator._teme_to_geodetic(vector, jd + fraction)
    return {
        "latitude": round(latitude, 4), "longitude": round(longitude, 4),
        "altitude": round(math.degrees(math.asin(up / distance)), 1),
        "azimuth": round(math.degrees(math.atan2(east, north)) % 360, 1),
        "range_km": round(distance), "vector": vector,
    }


def sunlit(vector, at):
    time = _time(at)
    sun = astronomy.RotateVector(astronomy.Rotation_EQJ_EQD(time), astronomy.GeoVector(astronomy.Body.Sun, time, True))
    length = sun.Length()
    direction = (sun.x / length, sun.y / length, sun.z / length)
    projection = sum(vector[i] * direction[i] for i in range(3))
    perpendicular = math.sqrt(max(0, sum(x*x for x in vector) - projection**2))
    # Cylindrical Earth shadow; intentionally not a brightness prediction.
    return projection > 0 or perpendicular > 6378.137


def calculate_passes(fields, observer, at):
    satellite = Satrec()
    omm.initialize(satellite, fields)
    current = position(satellite, observer, at)
    current.pop("vector")
    passes, samples, trail = [], [], []
    # One-minute sampling bounds CPU and storage. Record clipped passes
    # explicitly rather than inventing a rise before the search starts.
    for minute in range(1441):
        time = at + timedelta(minutes=minute)
        point = position(satellite, observer, time)
        if minute < MAX_TRAIL:
            trail.append({"latitude": point["latitude"], "longitude": point["longitude"], "time": time.isoformat()})
        if point["altitude"] >= 10:
            samples.append({"time": time.isoformat(), "altitude": point["altitude"], "azimuth": point["azimuth"], "vector": point["vector"]})
        if samples and (point["altitude"] < 10 or minute == 1440):
            peak = max(samples, key=lambda item: item["altitude"])
            peak_time = stamp(peak["time"])
            dark = horizon_at(observer, astronomy.Body.Sun, peak_time)["altitude"] < -6
            lit = sunlit(peak["vector"], peak_time)
            passes.append({
                "start": samples[0]["time"], "peak": peak["time"], "end": samples[-1]["time"],
                "max_elevation": peak["altitude"], "appearance_azimuth": samples[0]["azimuth"],
                "disappearance_azimuth": samples[-1]["azimuth"], "observer_dark": dark, "sunlit": lit,
                "visibility": "Possible" if dark and lit else "Not optically favorable",
                "clipped": minute == 1440 or samples[0]["time"] == at.isoformat(),
                "sky_path": [{key: item[key] for key in ("time", "altitude", "azimuth")} for item in samples[::max(1, math.ceil(len(samples) / 30))]],
            })
            samples = []
            if len(passes) >= MAX_PASSES:
                break
    return {
        **current, "passes": passes, "ground_track": trail[:MAX_TRAIL],
        "timestamp": int(at.timestamp()), "source": "CelesTrak / local SGP4",
        "element_epoch": fields["EPOCH"], "time_resolution_seconds": 60,
    }


class SatelliteCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name="Astronomy satellite passes", update_interval=timedelta(minutes=5))
        self.hass = hass
        config = entry.options.get("ephemeris", {})
        self.observer = astronomy.Observer(config.get("latitude", hass.config.latitude), config.get("longitude", hass.config.longitude), config.get("elevation", hass.config.elevation or 0))
        self.ids = selected_ids(entry.options.get("satellites", {}).get("norad_ids", [25544]))
        self.nasa = hass.data["nasa_astronomy"][entry.entry_id]["coordinator"]
        self.requests = {
            ident: ForecastRequest(async_get_clientsession(hass), "CelesTrak", f"https://celestrak.org/NORAD/elements/gp.php?CATNR={ident}&FORMAT=JSON", parse_elements(ident), timedelta(hours=12), timedelta(days=7))
            for ident in self.ids if ident != 25544
        }
        self._restored = False
        self._saved = None
        self._pass_cache = {}
        self.storage_key = f"nasa_astronomy.satellite_elements.{entry.entry_id}"

    async def _async_update_data(self):
        from homeassistant.helpers.storage import Store

        store = Store(self.hass, 1, self.storage_key)
        if not self._restored:
            saved = await store.async_load() or {}
            if 25544 in self.ids and saved.get("25544"):
                try:
                    elements = parse_elements(25544)([saved["25544"]["data"]])
                    self.nasa._iss_omm = elements
                    self.nasa._iss_omm_epoch = stamp(elements["EPOCH"])
                except (ValueError, TypeError, KeyError) as err:
                    _LOGGER.debug("Cached ISS elements rejected (%s)", type(err).__name__)
            for ident, request in self.requests.items():
                record = saved.get(str(ident))
                if record:
                    try:
                        request.data = request.parser([record["data"]])
                        request.last_success = stamp(record["last_success"])
                        request.next_attempt = request.last_success + request.interval
                    except (ValueError, TypeError, KeyError) as err:
                        _LOGGER.debug("Cached satellite elements rejected (%s)", type(err).__name__)
            self._restored = True
        payloads = await asyncio.gather(*(request.get() for request in self.requests.values()))
        fields = dict(zip(self.requests, payloads))
        if 25544 in self.ids:
            await self.nasa._refresh_iss_orbit_elements()
            fields[25544] = self.nasa._iss_omm
        saved = {str(ident): {"data": request.data, "last_success": request.last_success.isoformat()} for ident, request in self.requests.items() if request.last_success and request.data}
        if fields.get(25544):
            saved["25544"] = {"data": fields[25544]}
        if saved != self._saved:
            await store.async_save(saved)
            self._saved = saved
        return await self.hass.async_add_executor_job(self._calculate, fields)

    def _calculate(self, fields):
        now = datetime.now(timezone.utc)
        result = {}
        for ident, elements in fields.items():
            if elements is None:
                continue
            try:
                elements = parse_elements(ident)([elements])
                cached = self._pass_cache.get(ident)
                if cached is None or cached[0] != elements or now - cached[1] >= timedelta(minutes=30):
                    data = calculate_passes(elements, self.observer, now)
                    self._pass_cache[ident] = (elements, now, data)
                else:
                    data = dict(cached[2])
                    satellite = Satrec()
                    omm.initialize(satellite, elements)
                    current = position(satellite, self.observer, now)
                    current.pop("vector")
                    data.update(current)
                    data["timestamp"] = int(now.timestamp())
                    data["passes"] = [item for item in data["passes"] if stamp(item["end"]) > now]
                result[str(ident)] = {**data, "name": CATALOG.get(ident, f"NORAD {ident}"), "norad_id": ident,
                                     "stale": self.requests[ident].error is not None if ident in self.requests else not self.nasa._iss_omm_last_attempt_succeeded}
            except (ValueError, TypeError, KeyError, astronomy.Error) as err:
                _LOGGER.warning("Satellite calculation unavailable (%s)", type(err).__name__)
        return result
