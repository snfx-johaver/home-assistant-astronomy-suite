"""Deep-Sky Objects sensor module for the Astronomy Space Suite.

Pure-standard-library computation of altitude / azimuth / transit / rise-set and
a nightly "best viewing window" for a curated catalog of telescope targets. No
external dependencies and no API key — every coordinate is computed locally
(J2000), exactly like the suite's local ephemeris provider.

Each catalog object becomes a sensor whose state is its current altitude in
degrees, named ``sensor.nasa_astronomy_deepsky_<object>_altitude`` with rich
attributes (direction, status, best window, transit, magnitude, type,
constellation, season, info). A summary sensor,
``sensor.nasa_astronomy_deepsky_best_tonight``, ranks the catalog for "what to
look at right now" and renders two helper graphics (a top-down sky map and a
horizon panorama) plus a ``sky_objects`` attribute consumed by the 3D dome card.

The feature is opt-out via the config-flow/options ``deepsky`` section (enabled
by default). It ships **no personal data**: no aerial photo, no site horizon
scan, no hard-coded coordinates. Observer location comes from Home Assistant.
An advanced per-azimuth horizon profile is *optional* — if a user drops a
``nasa_astronomy_deepsky_horizon.json`` file in their ``/config`` folder the
"from your yard" overlays light up; otherwise a flat horizon is assumed.
"""
from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.util.dt as dt_util

from . import deepsky_panorama, deepsky_skymap
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)

# Default minimum altitude (deg) for a target to be considered telescope-usable
# above local haze / rooftops. Overridable in the options flow.
DEFAULT_MIN_ALT = 15.0

# Optional advanced horizon profile dropped by the user in /config. Update-safe
# (survives integration upgrades) and absent by default — keeps the feature
# free of personal data unless the user opts in.
HORIZON_FILENAME = "nasa_astronomy_deepsky_horizon.json"

# Where the runtime graphics are written. Co-located with the bundled cards so
# they are served from /local/community/astronomy-cards/ with no extra config.
WWW_SUBDIR = ("www", "community", "astronomy-cards")
YARDMAP_FILE = "nasa_astronomy_deepsky_yardmap.svg"
PANORAMA_FILE = "nasa_astronomy_deepsky_panorama.svg"
LOCAL_BASE = "/local/community/astronomy-cards"

# Curated catalog. Per-row:
# slug, display name, RA(deg, J2000), Dec(deg, J2000), magnitude, type,
# constellation, sun_alt_threshold(deg), best season, one-line description.
#
# sun_alt_threshold encodes how dark the sky must be for a worthwhile view:
#   -6  civil      (bright clusters / double stars punch through twilight)
#   -12 nautical   (globulars, bright planetary nebulae)
#   -15/-18 astro  (galaxies, faint nebulae need real darkness)
CATALOG = [
    ("m13", "M13 - Hercules Cluster", 250.421, 36.460, 5.8,
     "Globular cluster", "Hercules", -12.0, "Summer",
     "Half a million suns; the finest globular in northern skies"),
    ("m92", "M92", 259.281, 43.136, 6.4,
     "Globular cluster", "Hercules", -12.0, "Summer",
     "Bright, compact globular, often overlooked next to M13"),
    ("m5", "M5", 229.638, 2.081, 5.6,
     "Globular cluster", "Serpens", -12.0, "Summer",
     "One of the sky's oldest and richest globulars"),
    ("m57", "M57 - Ring Nebula", 283.396, 33.029, 8.8,
     "Planetary nebula", "Lyra", -12.0, "Summer",
     "Smoke-ring shell of a dying sun-like star"),
    ("m27", "M27 - Dumbbell Nebula", 299.901, 22.721, 7.4,
     "Planetary nebula", "Vulpecula", -12.0, "Summer",
     "Bright two-lobed planetary nebula, easy in small scopes"),
    ("albireo", "Albireo", 292.680, 27.960, 3.1,
     "Double star", "Cygnus", -6.0, "Summer",
     "Gorgeous gold-and-blue colour-contrast double"),
    ("mizar", "Mizar & Alcor", 200.981, 54.925, 2.2,
     "Double star", "Ursa Major", -6.0, "All year",
     "Naked-eye pair that splits further in a telescope"),
    ("dblcluster", "Double Cluster", 34.740, 57.130, 3.8,
     "Open clusters", "Perseus", -6.0, "Autumn",
     "NGC 869 & 884: twin swarms of young stars"),
    ("m31", "M31 - Andromeda Galaxy", 10.685, 41.269, 3.4,
     "Galaxy", "Andromeda", -15.0, "Autumn",
     "Nearest large galaxy, 2.5 million light-years away"),
    ("m45", "M45 - Pleiades", 56.601, 24.114, 1.6,
     "Open cluster", "Taurus", -6.0, "Winter",
     "The Seven Sisters; dazzling in binoculars and wide scopes"),
    ("m42", "M42 - Orion Nebula", 83.822, -5.391, 4.0,
     "Emission nebula", "Orion", -12.0, "Winter",
     "A stellar nursery; the showpiece nebula of the sky"),
    ("m44", "M44 - Beehive", 130.054, 19.667, 3.7,
     "Open cluster", "Cancer", -6.0, "Winter",
     "Big, bright naked-eye cluster, lovely at low power"),
    ("m81", "M81 - Bode's Galaxy", 148.888, 69.065, 6.9,
     "Galaxy", "Ursa Major", -15.0, "Spring",
     "Bright grand-design spiral, near-circumpolar from here"),
    ("m51", "M51 - Whirlpool Galaxy", 202.470, 47.195, 8.4,
     "Galaxy", "Canes Venatici", -18.0, "Spring",
     "Face-on spiral interacting with a small companion"),
]

# Solar-system bodies pulled from the suite's local ephemeris sensors for the
# overlay maps: (entity slug, display name, draw-kind).
SOLAR_BODIES = [
    ("sun", "Sun", "sun"),
    ("moon", "Moon", "moon"),
    ("mercury", "Mercury", "planet"),
    ("venus", "Venus", "planet"),
    ("mars", "Mars", "planet"),
    ("jupiter", "Jupiter", "planet"),
    ("saturn", "Saturn", "planet"),
    ("uranus", "Uranus", "planet"),
    ("neptune", "Neptune", "planet"),
]

_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


# --------------------------------------------------------------------------- #
# Pure-math helpers (no Home Assistant dependencies, J2000).
# --------------------------------------------------------------------------- #
def _jd(dt: datetime) -> float:
    """Julian Date from a timezone-aware datetime."""
    return dt.timestamp() / 86400.0 + 2440587.5


def _sun_radec(jd: float) -> tuple[float, float]:
    """Low-precision solar apparent RA/Dec in degrees (good for twilight)."""
    n = jd - 2451545.0
    L = math.radians((280.460 + 0.9856474 * n) % 360.0)
    g = math.radians((357.528 + 0.9856003 * n) % 360.0)
    lam = L + math.radians(1.915) * math.sin(g) + math.radians(0.020) * math.sin(2 * g)
    eps = math.radians(23.439 - 4.0e-7 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    return math.degrees(ra) % 360.0, math.degrees(dec)


def _lst_deg(jd: float, lon: float) -> float:
    """Local apparent sidereal time in degrees (longitude east-positive)."""
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360.0
    return (gmst + lon) % 360.0


def _altaz(ra: float, dec: float, lat: float, lst: float) -> tuple[float, float]:
    """Altitude and azimuth (deg) of an equatorial coordinate. Az from N, CW."""
    H = math.radians((lst - ra) % 360.0)
    latr = math.radians(lat)
    decr = math.radians(dec)
    sin_alt = math.sin(decr) * math.sin(latr) + math.cos(decr) * math.cos(latr) * math.cos(H)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = math.asin(sin_alt)
    cos_az = (math.sin(decr) - math.sin(alt) * math.sin(latr)) / (
        math.cos(alt) * math.cos(latr)
    )
    cos_az = max(-1.0, min(1.0, cos_az))
    az = math.degrees(math.acos(cos_az))
    if math.sin(H) > 0:
        az = 360.0 - az
    return math.degrees(alt), az % 360.0


def _sun_alt(jd: float, lat: float, lon: float) -> float:
    """Sun altitude in degrees."""
    ra, dec = _sun_radec(jd)
    alt, _ = _altaz(ra, dec, lat, _lst_deg(jd, lon))
    return alt


def _compass(az: float) -> str:
    return _COMPASS[int((az + 11.25) % 360.0 / 22.5)]


def _transit_after(now: datetime, ra: float, lon: float) -> datetime:
    """Next upper-transit time (object due south / highest)."""
    lst_now = _lst_deg(_jd(now), lon)
    d_deg = (ra - lst_now) % 360.0
    return now + timedelta(days=d_deg / 360.98564736629)


def _window(now: datetime, ra: float, dec: float, lat: float, lon: float,
            sun_thr: float, min_alt: float) -> tuple[datetime | None, datetime | None]:
    """First contiguous window in the next 24h where the object is above
    min_alt and the sky is dark enough (sun <= sun_thr)."""
    start: datetime | None = None
    end: datetime | None = None
    step = timedelta(minutes=10)
    horizon = now + timedelta(hours=24)
    t = now
    while t <= horizon:
        jd = _jd(t)
        alt, _ = _altaz(ra, dec, lat, _lst_deg(jd, lon))
        good = alt >= min_alt and _sun_alt(jd, lat, lon) <= sun_thr
        if good and start is None:
            start = t
        elif not good and start is not None:
            end = t
            break
        t += step
    if start is not None and end is None:
        end = horizon
    return start, end


def _window_text(now: datetime, start: datetime | None, end: datetime | None) -> str:
    if start is None or end is None:
        return "Not favourable tonight"
    le = dt_util.as_local(end).strftime("%H:%M")
    if start <= now:
        return f"Now until {le}"
    ls = dt_util.as_local(start).strftime("%H:%M")
    return f"{ls}-{le}"


def _short(name: str) -> str:
    """Short label for the maps (drop the ' - Common Name' suffix)."""
    return name.split(" - ")[0]


# --------------------------------------------------------------------------- #
# Optional per-azimuth horizon profile (advanced "from your yard" feature).
# --------------------------------------------------------------------------- #
def _load_horizon(path: str) -> dict | None:
    """Load an optional yard horizon profile from /config.

    Absent or malformed -> None, and every yard overlay degrades to a flat
    horizon. Never raises; keeps the feature self-contained and PII-free.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if (len(data.get("best", [])) == 360
                and len(data.get("typical", [])) == 360
                and len(data.get("worst", [])) == 360):
            return data
    except Exception:  # noqa: BLE001 - never break the platform over this
        pass
    return None


def _yard(horizon: dict | None, az: float,
          alt: float) -> tuple[bool, str, str, float | None]:
    """Verdict on whether an object clears the optional local horizon."""
    if horizon is None:
        return True, "", "", None
    a = int(round(az)) % 360
    best = horizon["best"][a]
    typ = horizon["typical"][a]
    worst = horizon["worst"][a]
    where = horizon.get("where", [""] * 360)[a] or ""
    spot = "centre of the yard" if where == "centre" else f"{where} side of the yard"
    if alt > worst:
        return True, "Clear from anywhere in the yard", "", typ
    if alt > typ:
        return True, "Clear from most of the yard", "", typ
    if alt > best:
        return True, f"Only from the {spot}", where, typ
    return False, "Blocked by your trees/house", where, typ


def _yard_tag(horizon: dict | None, clears: bool, status: str,
              where: str) -> str:
    """Compact yard label for dashboard tables ("" when no horizon)."""
    if horizon is None:
        return ""
    if not clears:
        return "Blocked"
    if status.startswith("Clear from anywhere"):
        return "Anywhere"
    if status.startswith("Clear from most"):
        return "Most spots"
    return f"{where or 'one spot'} only"


def _tier(yclear: bool, ystatus: str) -> str:
    """Map a yard verdict to a sky-map tier (clear / step / blocked)."""
    if not yclear:
        return "blocked"
    if ystatus.startswith("Only from"):
        return "step"
    return "clear"


def _write_text(path: str, text: str) -> None:
    """Write a graphic to /config/www (executor thread, never the event loop)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------------------- #
# Setup.
# --------------------------------------------------------------------------- #
async def async_setup_deepsky_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the deep-sky object sensors from the suite's config entry.

    Mirrors ``async_setup_ephemeris_sensors``: called from the sensor
    platform's ``async_setup_entry``. Gated by the ``deepsky`` options section,
    enabled by default.
    """
    cfg = entry.options.get("deepsky", entry.data.get("deepsky", {})) or {}
    if not cfg.get("enabled", True):
        _LOGGER.debug("Deep-sky feature disabled in options; skipping setup")
        return

    try:
        min_alt = float(cfg.get("min_altitude", DEFAULT_MIN_ALT))
    except (TypeError, ValueError):
        min_alt = DEFAULT_MIN_ALT
    try:
        max_objects = int(cfg.get("max_objects", 0) or 0)
    except (TypeError, ValueError):
        max_objects = 0

    horizon = await hass.async_add_executor_job(
        _load_horizon, hass.config.path(HORIZON_FILENAME)
    )
    if horizon is not None:
        _LOGGER.info("Deep-sky: loaded optional yard horizon profile")

    entities: list[SensorEntity] = [
        DeepSkyObjectSensor(hass, entry.entry_id, obj, min_alt, horizon)
        for obj in CATALOG
    ]
    entities.append(
        DeepSkyBestTonightSensor(hass, entry.entry_id, min_alt, max_objects, horizon)
    )
    async_add_entities(entities, update_before_add=True)


# --------------------------------------------------------------------------- #
# Entities.
# --------------------------------------------------------------------------- #
class _BaseDeepSky(SensorEntity):
    """Shared device + 60s self-refresh for the deep-sky entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_deepsky")},
            name="Deep-Sky Objects",
            manufacturer="Astronomy Space Suite",
            model="Curated telescope catalog",
            via_device=(DOMAIN, entry_id),
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(self.hass, self._async_tick, SCAN_INTERVAL)
        )

    async def _async_tick(self, _now: datetime) -> None:
        self.async_schedule_update_ha_state(force_refresh=True)


class DeepSkyObjectSensor(_BaseDeepSky):
    """One deep-sky catalog object; state = current altitude in degrees."""

    _attr_native_unit_of_measurement = "\u00b0"
    _attr_icon = "mdi:telescope"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry_id: str, obj: tuple,
                 min_alt: float, horizon: dict | None) -> None:
        super().__init__(hass, entry_id)
        self._obj = obj
        self._min_alt = min_alt
        self._horizon = horizon
        slug = obj[0]
        self._attr_unique_id = f"nasa_astronomy_deepsky_{slug}_altitude_{entry_id}"
        self.entity_id = f"sensor.nasa_astronomy_deepsky_{slug}_altitude"
        self._attr_name = f"Deep-Sky {obj[1]}"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        slug, name, ra, dec, mag, otype, const, sun_thr, season, blurb = self._obj
        lat = self.hass.config.latitude
        lon = self.hass.config.longitude
        now = dt_util.utcnow()
        jd = _jd(now)
        lst = _lst_deg(jd, lon)
        alt, az = _altaz(ra, dec, lat, lst)
        sun = _sun_alt(jd, lat, lon)
        transit = _transit_after(now, ra, lon)
        wstart, wend = _window(now, ra, dec, lat, lon, sun_thr, self._min_alt)

        if alt >= self._min_alt and sun <= sun_thr:
            status = "Observable now"
        elif alt >= self._min_alt:
            status = "Up - sky too bright"
        elif wstart is not None:
            status = "Rises into view later"
        else:
            status = "Not favourable tonight"

        yclear, ystatus, ywhere, yhor = _yard(self._horizon, az, alt)

        self._attr_native_value = round(alt, 1)
        attrs = {
            "object": name,
            "type": otype,
            "constellation": const,
            "magnitude": mag,
            "altitude": round(alt, 1),
            "azimuth": round(az, 1),
            "direction": _compass(az),
            "status": status,
            "best_window": _window_text(now, wstart, wend),
            "transit_time": dt_util.as_local(transit).strftime("%H:%M"),
            "max_altitude": round(90.0 - abs(lat - dec), 1),
            "best_season": season,
            "info": blurb,
        }
        if self._horizon is not None:
            attrs.update({
                "yard_visible": yclear,
                "yard_status": ystatus,
                "yard_where": ywhere,
                "obstruction_alt": round(yhor, 1) if yhor is not None else None,
            })
        self._attr_extra_state_attributes = attrs


class DeepSkyBestTonightSensor(_BaseDeepSky):
    """Summary sensor ranking the catalog and rendering the helper graphics."""

    _attr_icon = "mdi:star-shooting"
    _attr_name = "Deep-Sky Best Tonight"
    _attr_native_unit_of_measurement = "objects"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, entry_id: str, min_alt: float,
                 max_objects: int, horizon: dict | None) -> None:
        super().__init__(hass, entry_id)
        self._min_alt = min_alt
        self._max_objects = max_objects
        self._horizon = horizon
        self._attr_unique_id = f"nasa_astronomy_deepsky_best_tonight_{entry_id}"
        self.entity_id = "sensor.nasa_astronomy_deepsky_best_tonight"
        self._attr_native_value = 0
        self._attr_extra_state_attributes = {}
        self._map_rev = 0
        self._last_svg: str | None = None
        self._pano_rev = 0
        self._last_pano: str | None = None

    async def async_update(self) -> None:
        lat = self.hass.config.latitude
        lon = self.hass.config.longitude
        now = dt_util.utcnow()
        jd = _jd(now)
        lst = _lst_deg(jd, lon)
        sun = _sun_alt(jd, lat, lon)

        rows: list[tuple[tuple, dict]] = []
        positions: list[dict] = []
        observable = 0
        observable_yard = 0
        for obj in CATALOG:
            slug, name, ra, dec, mag, otype, const, sun_thr, season, blurb = obj
            alt, az = _altaz(ra, dec, lat, lst)
            wstart, wend = _window(now, ra, dec, lat, lon, sun_thr, self._min_alt)
            now_ok = alt >= self._min_alt and sun <= sun_thr
            yclear, ystatus, ywhere, _yhor = _yard(self._horizon, az, alt)
            if now_ok:
                observable += 1
            if now_ok and yclear:
                observable_yard += 1
                sortkey = (0, -alt)
            elif now_ok:
                sortkey = (1, -alt)
            elif wstart is not None:
                sortkey = (2, wstart.timestamp())
            else:
                sortkey = (3, -alt)
            row = {
                "name": name,
                "type": otype,
                "altitude": round(alt, 1),
                "direction": _compass(az),
                "window": _window_text(now, wstart, wend),
                "status": "Now" if now_ok else (
                    "Up" if alt >= self._min_alt else (
                        "Later" if wstart is not None else "-")),
            }
            if self._horizon is not None:
                row["yard"] = _yard_tag(self._horizon, yclear, ystatus, ywhere)
            rows.append((sortkey, row))
            if alt > 0:
                positions.append({
                    "short": _short(name), "az": az, "alt": alt,
                    "kind": "deepsky", "tier": _tier(yclear, ystatus),
                    "where": ywhere, "bright": now_ok,
                })
        rows.sort(key=lambda r: r[0])

        # Solar-system bodies from the suite's local ephemeris sensors. States
        # hold the float altitude/azimuth. Missing/unknown -> skip silently.
        for slug, disp, kind in SOLAR_BODIES:
            sa = self.hass.states.get(
                f"sensor.nasa_astronomy_ephemeris_{slug}_altitude")
            sz = self.hass.states.get(
                f"sensor.nasa_astronomy_ephemeris_{slug}_azimuth")
            if sa is None or sz is None:
                continue
            try:
                balt = float(sa.state)
                baz = float(sz.state)
            except (TypeError, ValueError):
                continue
            if balt <= 0:
                continue
            yc, ys, yw, _ = _yard(self._horizon, baz, balt)
            positions.append({
                "short": disp, "az": baz, "alt": balt, "kind": kind,
                "tier": _tier(yc, ys), "where": yw,
                "bright": True if kind == "sun" else balt >= 10,
            })

        now_local = dt_util.as_local(now).strftime("%a %d %b %H:%M")

        # Render the top-down sky map (cache-busted via map_rev).
        try:
            typ = self._horizon["typical"] if self._horizon else []
            svg = deepsky_skymap.render_svg(positions, typ, now_local)
            if svg != self._last_svg:
                self._last_svg = svg
                self._map_rev = int(now.timestamp())
                path = self.hass.config.path(*WWW_SUBDIR, YARDMAP_FILE)
                await self.hass.async_add_executor_job(_write_text, path, svg)
        except Exception:  # noqa: BLE001 - never break the sensor over a draw
            _LOGGER.debug("Deep-sky sky-map render failed", exc_info=True)

        # Render the horizon panorama (stand-and-turn-around skyline strip).
        try:
            pano = deepsky_panorama.render(positions, self._horizon, now_local)
            if pano != self._last_pano:
                self._last_pano = pano
                self._pano_rev = int(now.timestamp())
                ppath = self.hass.config.path(*WWW_SUBDIR, PANORAMA_FILE)
                await self.hass.async_add_executor_job(_write_text, ppath, pano)
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Deep-sky panorama render failed", exc_info=True)

        table = [r[1] for r in rows]
        if self._max_objects:
            table = table[:self._max_objects]

        sky_objects = [
            {"short": p["short"], "kind": p["kind"],
             "az": round(p["az"], 1), "alt": round(p["alt"], 1),
             "tier": p["tier"], "bright": bool(p.get("bright"))}
            for p in positions
        ]

        self._attr_native_value = observable
        attrs = {
            "observable_now": observable,
            "map_rev": self._map_rev,
            "pano_rev": self._pano_rev,
            "map_url": f"{LOCAL_BASE}/{YARDMAP_FILE}?v={self._map_rev}",
            "pano_url": f"{LOCAL_BASE}/{PANORAMA_FILE}?v={self._pano_rev}",
            "objects": table,
            "sky_now": now_local,
            "sky_objects": sky_objects,
        }
        if self._horizon is not None:
            attrs["observable_now_yard"] = observable_yard
            attrs["sky_horizon"] = self._horizon["typical"]
        self._attr_extra_state_attributes = attrs
