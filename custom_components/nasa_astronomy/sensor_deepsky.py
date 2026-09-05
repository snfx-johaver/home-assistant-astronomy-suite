"""Deep-Sky Objects sensor platform for Astronomy Space Suite.

Provides a curated catalog of deep-sky telescope targets as sensors.
Computes live altitude/azimuth, transit time, best observing window,
magnitude, type, and season from HA's configured lat/lon.

Pure stdlib — no external API, no requirements.
Consumes existing ephemeris sensors for planet/sun/moon overlays.
"""
from __future__ import annotations

from .const import DOMAIN, INTEGRATION_VERSION

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEGREE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)

# ─── Deep-Sky Object Catalog ───────────────────────────────────────────────
# Curated list of best amateur targets
# Format: (name, ra_hours, dec_degrees, magnitude, type, constellation, season, description)
DSO_CATALOG = [
    ("M31", 0.712, 41.27, 3.4, "Galaxy", "Andromeda", "autumn", "Andromeda Galaxy — nearest large spiral"),
    ("M42", 5.588, -5.39, 4.0, "Nebula", "Orion", "winter", "Orion Nebula — brightest diffuse nebula"),
    ("M45", 3.787, 24.12, 1.6, "Cluster", "Taurus", "winter", "Pleiades — iconic open cluster"),
    ("M13", 16.695, 36.46, 5.8, "Cluster", "Hercules", "summer", "Great Globular Cluster in Hercules"),
    ("M51", 13.498, 47.20, 8.4, "Galaxy", "Canes Venatici", "spring", "Whirlpool Galaxy — face-on spiral"),
    ("M57", 18.893, 33.03, 8.8, "Nebula", "Lyra", "summer", "Ring Nebula — planetary nebula"),
    ("M8", 18.063, -24.38, 6.0, "Nebula", "Sagittarius", "summer", "Lagoon Nebula — bright emission"),
    ("M27", 19.994, 22.72, 7.5, "Nebula", "Vulpecula", "summer", "Dumbbell Nebula — large planetary"),
    ("M81", 9.926, 69.07, 6.9, "Galaxy", "Ursa Major", "spring", "Bode's Galaxy — grand design spiral"),
    ("M82", 9.926, 69.68, 8.4, "Galaxy", "Ursa Major", "spring", "Cigar Galaxy — starburst galaxy"),
    ("M101", 14.054, 54.35, 7.9, "Galaxy", "Ursa Major", "spring", "Pinwheel Galaxy — face-on spiral"),
    ("M104", 12.666, -11.62, 8.0, "Galaxy", "Virgo", "spring", "Sombrero Galaxy — edge-on with dust lane"),
    ("NGC 7000", 20.988, 44.33, 4.0, "Nebula", "Cygnus", "summer", "North America Nebula"),
    ("M17", 18.346, -16.18, 6.0, "Nebula", "Sagittarius", "summer", "Omega/Swan Nebula"),
    ("M20", 18.044, -23.03, 6.3, "Nebula", "Sagittarius", "summer", "Trifid Nebula"),
    ("NGC 869", 2.319, 57.13, 5.3, "Cluster", "Perseus", "autumn", "Double Cluster (h Persei)"),
    ("NGC 884", 2.371, 57.15, 6.1, "Cluster", "Perseus", "autumn", "Double Cluster (χ Persei)"),
    ("M1", 5.576, 22.01, 8.4, "Nebula", "Taurus", "winter", "Crab Nebula — supernova remnant"),
    ("M33", 1.564, 30.66, 5.7, "Galaxy", "Triangulum", "autumn", "Triangulum Galaxy — Local Group spiral"),
    ("M44", 8.671, 19.67, 3.7, "Cluster", "Cancer", "spring", "Beehive Cluster — large open cluster"),
    ("NGC 6992", 20.821, 31.73, 7.0, "Nebula", "Cygnus", "summer", "Veil Nebula (Eastern Arc)"),
    ("M22", 18.603, -23.90, 5.1, "Cluster", "Sagittarius", "summer", "Bright globular near galactic center"),
    ("M3", 13.703, 28.38, 6.2, "Cluster", "Canes Venatici", "spring", "Bright northern globular cluster"),
    ("M5", 15.310, 2.08, 5.7, "Cluster", "Serpens", "summer", "Large bright globular cluster"),
    ("NGC 253", 0.793, -25.29, 7.2, "Galaxy", "Sculptor", "autumn", "Sculptor Galaxy — bright edge-on"),
    ("M16", 18.314, -13.81, 6.0, "Nebula", "Serpens", "summer", "Eagle Nebula — Pillars of Creation"),
    ("IC 434", 5.681, -2.46, 7.3, "Nebula", "Orion", "winter", "Horsehead Nebula region"),
    ("M35", 6.148, 24.33, 5.3, "Cluster", "Gemini", "winter", "Rich open cluster in Gemini"),
    ("M47", 7.611, -14.49, 4.4, "Cluster", "Puppis", "winter", "Bright scattered open cluster"),
    ("M78", 5.779, 0.05, 8.3, "Nebula", "Orion", "winter", "Bright reflection nebula"),
]

# Sensors per DSO object
DSO_OBJECT_SENSORS = [
    {"key": "altitude", "name": "Altitude", "unit": DEGREE, "icon": "mdi:angle-acute", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "azimuth", "name": "Azimuth", "unit": DEGREE, "icon": "mdi:compass", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "transit_time", "name": "Transit", "unit": None, "icon": "mdi:arrow-up-bold", "state_class": None},
    {"key": "visible", "name": "Visible", "unit": None, "icon": "mdi:eye", "state_class": None},
]


def _julian_date(dt: datetime) -> float:
    """Compute Julian Date from a datetime (converts to UTC first)."""
    utc = dt.astimezone(timezone.utc)
    a = (14 - utc.month) // 12
    y = utc.year + 4800 - a
    m = utc.month + 12 * a - 3
    jdn = utc.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (utc.hour - 12) / 24.0 + utc.minute / 1440.0 + utc.second / 86400.0


def _local_sidereal_time(jd: float, longitude: float) -> float:
    """Compute local sidereal time in hours."""
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t * t
    gmst = gmst % 360
    lst = (gmst + longitude) / 15.0
    return lst % 24


def _compute_alt_az(ra_hours: float, dec_deg: float, lat: float, lon: float, dt: datetime) -> tuple[float, float]:
    """Compute altitude and azimuth for a fixed RA/Dec at given location and time."""
    jd = _julian_date(dt)
    lst = _local_sidereal_time(jd, lon)

    # Hour angle in degrees
    ha = (lst - ra_hours) * 15.0
    ha_rad = math.radians(ha)
    dec_rad = math.radians(dec_deg)
    lat_rad = math.radians(lat)

    # Altitude
    sin_alt = math.sin(dec_rad) * math.sin(lat_rad) + math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad)
    alt = math.degrees(math.asin(max(-1, min(1, sin_alt))))

    # Azimuth
    cos_az = (math.sin(dec_rad) - math.sin(math.radians(alt)) * math.sin(lat_rad)) / (
        math.cos(math.radians(alt)) * math.cos(lat_rad) + 1e-10
    )
    cos_az = max(-1, min(1, cos_az))
    az = math.degrees(math.acos(cos_az))
    if math.sin(ha_rad) > 0:
        az = 360 - az

    return round(alt, 1), round(az, 1)


def _compute_transit_time(ra_hours: float, lon: float, dt: datetime) -> str:
    """Compute approximate transit time (when object is highest) for tonight."""
    jd = _julian_date(dt.replace(hour=0, minute=0, second=0))
    lst_midnight = _local_sidereal_time(jd, lon)
    # Time until RA crosses meridian
    transit_lst = ra_hours
    diff = (transit_lst - lst_midnight) % 24
    transit_utc = dt.replace(hour=0, minute=0, second=0) + timedelta(hours=diff * 0.9973)  # sidereal correction
    local_time = transit_utc.astimezone(dt.tzinfo) if dt.tzinfo else transit_utc
    return local_time.strftime("%H:%M")


def _compute_best_window(ra_hours: float, dec_deg: float, lat: float, lon: float, dt: datetime) -> dict:
    """Find the best viewing window tonight (highest altitude period)."""
    # Check every 30 minutes from sunset (~18:00) to sunrise (~06:00)
    base = dt.replace(hour=18, minute=0, second=0, microsecond=0)
    best_alt = -90
    best_time = base
    window_start = None
    window_end = None
    min_alt_threshold = 15  # degrees above horizon

    for i in range(25):  # 18:00 to 06:00 in 30-min steps
        check_time = base + timedelta(minutes=i * 30)
        alt, _ = _compute_alt_az(ra_hours, dec_deg, lat, lon, check_time)
        if alt > min_alt_threshold:
            if window_start is None:
                window_start = check_time
            window_end = check_time
        if alt > best_alt:
            best_alt = alt
            best_time = check_time

    return {
        "peak_altitude": round(best_alt, 1),
        "peak_time": best_time.strftime("%H:%M"),
        "window_start": window_start.strftime("%H:%M") if window_start else None,
        "window_end": window_end.strftime("%H:%M") if window_end else None,
    }


def _score_object(alt: float, magnitude: float, obj_type: str) -> int:
    """Score an object 0–100 for "how good is it to observe right now"."""
    if alt < 0:
        return 0
    # Altitude score (peaks around 60°)
    alt_score = min(alt / 60.0, 1.0) * 50
    # Magnitude score (brighter = better, scale from mag 1 to 10)
    mag_score = max(0, (10 - magnitude) / 9) * 30
    # Type bonus
    type_bonus = {"Nebula": 10, "Cluster": 8, "Galaxy": 12}.get(obj_type, 5)
    # High altitude bonus
    high_bonus = 10 if alt > 45 else 0

    return min(100, int(alt_score + mag_score + type_bonus + high_bonus))


class DeepSkyProvider:
    """Computes deep-sky object positions from the catalog."""

    def __init__(self, latitude: float, longitude: float, min_altitude: float = 15, max_objects: int = 30):
        self.lat = latitude
        self.lon = longitude
        self.min_altitude = min_altitude
        self.max_objects = max_objects

    def compute_all(self) -> dict[str, Any]:
        """Compute current positions and scores for all catalog objects."""
        now = datetime.now(timezone.utc).astimezone()
        data: dict[str, Any] = {}

        scored_objects = []

        for name, ra, dec, mag, obj_type, constellation, season, description in DSO_CATALOG[:self.max_objects]:
            alt, az = _compute_alt_az(ra, dec, self.lat, self.lon, now)
            transit = _compute_transit_time(ra, self.lon, now)
            visible = alt > self.min_altitude
            score = _score_object(alt, mag, obj_type)
            best_window = _compute_best_window(ra, dec, self.lat, self.lon, now)

            obj_key = name.lower().replace(" ", "_").replace("-", "_")
            data[obj_key] = {
                "name": name,
                "altitude": alt,
                "azimuth": az,
                "transit_time": transit,
                "visible": "Yes" if visible else "No",
                "magnitude": mag,
                "type": obj_type,
                "constellation": constellation,
                "season": season,
                "description": description,
                "score": score,
                "best_window": best_window,
                "ra_hours": ra,
                "dec_degrees": dec,
            }

            if visible:
                scored_objects.append((name, score, alt, obj_type, constellation, description, best_window))

        # Best tonight summary
        scored_objects.sort(key=lambda x: x[1], reverse=True)
        top3 = scored_objects[:3]
        data["_best_tonight"] = {
            "count_visible": len(scored_objects),
            "top_objects": [
                {
                    "name": obj[0],
                    "score": obj[1],
                    "altitude": obj[2],
                    "type": obj[3],
                    "constellation": obj[4],
                    "description": obj[5],
                    "peak_time": obj[6].get("peak_time", ""),
                }
                for obj in top3
            ],
            "summary": f"{len(scored_objects)} objects visible" + (
                f" — best: {top3[0][0]} ({top3[0][1]}%)" if top3 else ""
            ),
        }

        return data


class DeepSkyCoordinator(DataUpdateCoordinator):
    """Coordinator for deep-sky calculations."""

    def __init__(self, hass: HomeAssistant, provider: DeepSkyProvider):
        super().__init__(
            hass,
            _LOGGER,
            name="Astronomy Deep Sky",
            update_interval=SCAN_INTERVAL,
        )
        self.provider = provider

    async def _async_update_data(self) -> dict[str, Any]:
        """Run calculations in executor thread."""
        return await self.hass.async_add_executor_job(self.provider.compute_all)


async def async_setup_deepsky_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up deep-sky sensors from config entry."""
    deepsky_config = entry.options.get("deepsky", entry.data.get("deepsky", {}))
    # Default to enabled if no config exists
    if not deepsky_config:
        deepsky_config = {"enabled": True, "min_altitude": 15, "max_objects": 30}
    if not deepsky_config.get("enabled", True):
        return

    lat = hass.config.latitude
    lon = hass.config.longitude
    min_alt = deepsky_config.get("min_altitude", 15)
    max_objects = deepsky_config.get("max_objects", 30)

    provider = DeepSkyProvider(
        latitude=lat,
        longitude=lon,
        min_altitude=min_alt,
        max_objects=max_objects,
    )

    coordinator = DeepSkyCoordinator(hass, provider)
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id]["deepsky_coordinator"] = coordinator

    entities: list[DeepSkySensor] = []

    # Create sensors for each DSO in catalog
    for name, ra, dec, mag, obj_type, constellation, season, description in DSO_CATALOG[:max_objects]:
        obj_key = name.lower().replace(" ", "_").replace("-", "_")
        for sdef in DSO_OBJECT_SENSORS:
            entities.append(
                DeepSkySensor(
                    coordinator=coordinator,
                    obj_key=obj_key,
                    obj_name=name,
                    sensor_key=sdef["key"],
                    sensor_name=sdef["name"],
                    unit=sdef["unit"],
                    icon=sdef["icon"],
                    state_class=sdef["state_class"],
                    entry_id=entry.entry_id,
                    extra_attrs={
                        "object_name": name,
                        "object_key": obj_key,
                        "magnitude": mag,
                        "type": obj_type,
                        "constellation": constellation,
                        "season": season,
                        "description": description,
                    },
                )
            )

    # Best Tonight summary sensor
    entities.append(
        DeepSkyBestTonightSensor(coordinator, entry.entry_id)
    )

    async_add_entities(entities)
    _LOGGER.info("Registered %d deep-sky sensors for %d objects", len(entities), min(max_objects, len(DSO_CATALOG)))


class DeepSkySensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for a deep-sky object metric."""

    def __init__(
        self,
        coordinator: DeepSkyCoordinator,
        obj_key: str,
        obj_name: str,
        sensor_key: str,
        sensor_name: str,
        unit: str | None,
        icon: str,
        state_class: SensorStateClass | None,
        entry_id: str,
        extra_attrs: dict | None = None,
    ):
        super().__init__(coordinator)
        self._obj_key = obj_key
        self._sensor_key = sensor_key
        self._extra_attrs = extra_attrs or {}
        self._attr_name = f"Deep Sky {obj_name} {sensor_name}"
        self._attr_unique_id = f"nasa_astronomy_deepsky_{obj_key}_{sensor_key}_{entry_id}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        # `False` SELECTS Home Assistant's legacy naming — it does NOT opt out of
        # the device prefix. Legacy naming composes friendly_name for a
        # device-attached entity as "<device name> <entity name>". Confirmed
        # against the live entity registry:
        #     device name          = "Astronomy Space Suite" (name_by_user: null)
        #     entity original_name = "Deep Sky M31 Altitude" (no prefix stored)
        #     has_entity_name      = False on all 121 entities, 0 custom names
        #  => friendly_name        = "Astronomy Space Suite Deep Sky M31 Altitude"
        # The prefix is therefore HA behaving as designed, not a defect here.
        #
        # Considered and rejected: setting this True with a short _attr_name is
        # the textbook fix, but it would rewrite friendly_name for all 121
        # entities on every existing install, breaking dashboards and
        # automations. Cards read the `object_name` attribute below instead.
        self._attr_has_entity_name = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self.entity_id = f"sensor.nasa_astronomy_deepsky_{obj_key}_{sensor_key}"

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        if not self.coordinator.data:
            return None
        obj_data = self.coordinator.data.get(self._obj_key)
        if not obj_data:
            return None
        return obj_data.get(self._sensor_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = dict(self._extra_attrs)
        if self.coordinator.data:
            obj_data = self.coordinator.data.get(self._obj_key, {})
            attrs["score"] = obj_data.get("score", 0)
            # Canonical designation (e.g. "M31", "NGC 7000"). Cards read this instead
            # of parsing friendly_name, which may be prefixed with the device name.
            if obj_data.get("name"):
                attrs["object_name"] = obj_data["name"]
            best = obj_data.get("best_window", {})
            if best:
                attrs["peak_altitude"] = best.get("peak_altitude")
                attrs["peak_time"] = best.get("peak_time")
                attrs["window_start"] = best.get("window_start")
                attrs["window_end"] = best.get("window_end")
        return attrs


class DeepSkyBestTonightSensor(CoordinatorEntity, SensorEntity):
    """Summary sensor: best deep-sky objects visible tonight."""

    def __init__(self, coordinator: DeepSkyCoordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = "Deep Sky Best Tonight"
        self._attr_unique_id = f"nasa_astronomy_deepsky_best_tonight_{entry_id}"
        self._attr_icon = "mdi:telescope"
        # See DeepSkySensor: legacy naming prepends the device name. Left as-is
        # deliberately so existing installs keep their entity names.
        self._attr_has_entity_name = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self.entity_id = "sensor.nasa_astronomy_deepsky_best_tonight"

    @property
    def native_value(self) -> str | None:
        """Return summary string."""
        if not self.coordinator.data:
            return None
        best = self.coordinator.data.get("_best_tonight", {})
        return best.get("summary", "No objects visible")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return top objects as attributes."""
        if not self.coordinator.data:
            return {}
        best = self.coordinator.data.get("_best_tonight", {})
        return {
            "count_visible": best.get("count_visible", 0),
            "top_objects": best.get("top_objects", []),
        }
