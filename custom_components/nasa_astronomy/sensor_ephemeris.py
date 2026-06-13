"""Ephemeris sensor platform for Astronomy Space Suite.

Dynamically registers sensors based on user configuration.
Each enabled celestial body gets a set of sensors.
Never interferes with existing NASA-based sensors.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    UnitOfLength,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .providers.openastronomy_ephemeris import (
    BODY_LIST,
    OpenAstronomyEphemerisProvider,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)

# Sensor definitions per body type
SUN_SENSORS = [
    {"key": "altitude", "name": "Altitude", "unit": DEGREE, "icon": "mdi:angle-acute", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "azimuth", "name": "Azimuth", "unit": DEGREE, "icon": "mdi:compass", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "right_ascension", "name": "Right Ascension", "unit": DEGREE, "icon": "mdi:axis-x-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "declination", "name": "Declination", "unit": DEGREE, "icon": "mdi:axis-y-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "distance_au", "name": "Distance", "unit": "AU", "icon": "mdi:map-marker-distance", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "angular_diameter_arcmin", "name": "Angular Diameter", "unit": "arcmin", "icon": "mdi:circle-outline", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "solar_noon", "name": "Solar Noon", "unit": "h UTC", "icon": "mdi:weather-sunny", "state_class": None},
    {"key": "civil_dawn", "name": "Civil Dawn", "unit": "h UTC", "icon": "mdi:weather-sunset-up", "state_class": None},
    {"key": "civil_dusk", "name": "Civil Dusk", "unit": "h UTC", "icon": "mdi:weather-sunset-down", "state_class": None},
    {"key": "nautical_dawn", "name": "Nautical Dawn", "unit": "h UTC", "icon": "mdi:weather-night", "state_class": None},
    {"key": "nautical_dusk", "name": "Nautical Dusk", "unit": "h UTC", "icon": "mdi:weather-night", "state_class": None},
    {"key": "astronomical_dawn", "name": "Astronomical Dawn", "unit": "h UTC", "icon": "mdi:star", "state_class": None},
    {"key": "astronomical_dusk", "name": "Astronomical Dusk", "unit": "h UTC", "icon": "mdi:star", "state_class": None},
]

MOON_SENSORS = [
    {"key": "altitude", "name": "Altitude", "unit": DEGREE, "icon": "mdi:angle-acute", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "azimuth", "name": "Azimuth", "unit": DEGREE, "icon": "mdi:compass", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "right_ascension", "name": "Right Ascension", "unit": DEGREE, "icon": "mdi:axis-x-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "declination", "name": "Declination", "unit": DEGREE, "icon": "mdi:axis-y-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "distance_km", "name": "Distance", "unit": "km", "icon": "mdi:map-marker-distance", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "angular_diameter_arcmin", "name": "Angular Diameter", "unit": "arcmin", "icon": "mdi:circle-outline", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "phase_angle", "name": "Phase Angle", "unit": DEGREE, "icon": "mdi:moon-waning-crescent", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "illumination_pct", "name": "Illumination", "unit": "%", "icon": "mdi:brightness-percent", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "next_full_moon", "name": "Next Full Moon", "unit": None, "icon": "mdi:moon-full", "state_class": None},
    {"key": "next_new_moon", "name": "Next New Moon", "unit": None, "icon": "mdi:moon-new", "state_class": None},
]

PLANET_SENSORS = [
    {"key": "altitude", "name": "Altitude", "unit": DEGREE, "icon": "mdi:angle-acute", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "azimuth", "name": "Azimuth", "unit": DEGREE, "icon": "mdi:compass", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "right_ascension", "name": "Right Ascension", "unit": DEGREE, "icon": "mdi:axis-x-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "declination", "name": "Declination", "unit": DEGREE, "icon": "mdi:axis-y-arrow", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "distance_au", "name": "Distance", "unit": "AU", "icon": "mdi:map-marker-distance", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "illumination_pct", "name": "Illumination", "unit": "%", "icon": "mdi:brightness-percent", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "phase_angle", "name": "Phase Angle", "unit": DEGREE, "icon": "mdi:circle-half-full", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "angular_diameter_arcsec", "name": "Angular Diameter", "unit": "arcsec", "icon": "mdi:circle-outline", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "rise", "name": "Rise", "unit": "h UTC", "icon": "mdi:arrow-up-circle", "state_class": None},
    {"key": "transit", "name": "Transit", "unit": "h UTC", "icon": "mdi:arrow-up-bold", "state_class": None},
    {"key": "set", "name": "Set", "unit": "h UTC", "icon": "mdi:arrow-down-circle", "state_class": None},
    {"key": "visibility_start", "name": "Visibility Start", "unit": "h UTC", "icon": "mdi:eye", "state_class": None},
    {"key": "visibility_end", "name": "Visibility End", "unit": "h UTC", "icon": "mdi:eye-off", "state_class": None},
]

SKY_SENSORS = [
    {"key": "twilight_phase", "name": "Twilight Phase", "unit": None, "icon": "mdi:theme-light-dark", "state_class": None},
    {"key": "is_astronomical_night", "name": "Astronomical Night", "unit": None, "icon": "mdi:weather-night", "state_class": None},
    {"key": "is_sun_above_horizon", "name": "Sun Above Horizon", "unit": None, "icon": "mdi:white-balance-sunny", "state_class": None},
    {"key": "is_moon_above_horizon", "name": "Moon Above Horizon", "unit": None, "icon": "mdi:moon-waxing-crescent", "state_class": None},
    {"key": "day_length_hours", "name": "Day Length", "unit": "h", "icon": "mdi:weather-sunny", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "night_length_hours", "name": "Night Length", "unit": "h", "icon": "mdi:weather-night", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "local_sidereal_time_hours", "name": "Local Sidereal Time", "unit": "h", "icon": "mdi:clock-star-four-points", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "julian_date", "name": "Julian Date", "unit": None, "icon": "mdi:calendar-clock", "state_class": SensorStateClass.MEASUREMENT},
    {"key": "equation_of_time_minutes", "name": "Equation of Time", "unit": "min", "icon": "mdi:clock-fast", "state_class": SensorStateClass.MEASUREMENT},
]

BODY_ICONS = {
    "sun": "mdi:white-balance-sunny",
    "moon": "mdi:moon-waning-crescent",
    "mercury": "mdi:planet-mercury",  # Fallback to mdi:circle-small
    "venus": "mdi:gender-female",
    "mars": "mdi:gender-male",
    "jupiter": "mdi:planet-jupiter",  # Fallback
    "saturn": "mdi:planet-saturn",  # Fallback
    "uranus": "mdi:earth",
    "neptune": "mdi:water",
}


class EphemerisCoordinator(DataUpdateCoordinator):
    """Coordinator for ephemeris data updates."""

    def __init__(self, hass: HomeAssistant, provider: OpenAstronomyEphemerisProvider):
        super().__init__(
            hass,
            _LOGGER,
            name="Astronomy Ephemeris",
            update_interval=SCAN_INTERVAL,
        )
        self.provider = provider

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from provider (runs in executor for CPU-bound math)."""
        return await self.hass.async_add_executor_job(self._fetch_all)

    def _fetch_all(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for body in self.provider.enabled_bodies:
            result = self.provider.get_ephemeris(body)
            if result:
                data[body] = result
        # Sky conditions (always calculated if any body is enabled)
        if self.provider.enabled_bodies:
            data["sky"] = self.provider.get_sky_conditions()
        return data


async def async_setup_ephemeris_sensors(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ephemeris sensors from config entry."""
    ephemeris_config = entry.options.get("ephemeris", entry.data.get("ephemeris", {}))
    if not ephemeris_config.get("enabled", False):
        return

    lat = ephemeris_config.get("latitude", hass.config.latitude)
    lon = ephemeris_config.get("longitude", hass.config.longitude)
    elevation = ephemeris_config.get("elevation", hass.config.elevation or 0)
    update_interval = ephemeris_config.get("update_interval", 3600)
    bodies_config = ephemeris_config.get("bodies", {})

    provider = OpenAstronomyEphemerisProvider(
        latitude=lat,
        longitude=lon,
        elevation=elevation,
        update_interval=update_interval,
        enabled_bodies=bodies_config,
    )

    coordinator = EphemerisCoordinator(hass, provider)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator for the card to use
    hass.data[DOMAIN][entry.entry_id]["ephemeris_coordinator"] = coordinator

    entities: list[EphemerisSensor] = []

    for body in provider.enabled_bodies:
        if body == "sun":
            sensor_defs = SUN_SENSORS
        elif body == "moon":
            sensor_defs = MOON_SENSORS
        else:
            sensor_defs = PLANET_SENSORS

        for sdef in sensor_defs:
            entities.append(
                EphemerisSensor(
                    coordinator=coordinator,
                    body=body,
                    sensor_key=sdef["key"],
                    sensor_name=sdef["name"],
                    unit=sdef["unit"],
                    icon=sdef["icon"],
                    state_class=sdef["state_class"],
                    entry_id=entry.entry_id,
                )
            )

    # Sky condition sensors (always if any body enabled)
    for sdef in SKY_SENSORS:
        entities.append(
            EphemerisSensor(
                coordinator=coordinator,
                body="sky",
                sensor_key=sdef["key"],
                sensor_name=sdef["name"],
                unit=sdef["unit"],
                icon=sdef["icon"],
                state_class=sdef["state_class"],
                entry_id=entry.entry_id,
            )
        )

    async_add_entities(entities)
    _LOGGER.info("Registered %d ephemeris sensors for bodies: %s", len(entities), provider.enabled_bodies)


class EphemerisSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for an ephemeris metric."""

    def __init__(
        self,
        coordinator: EphemerisCoordinator,
        body: str,
        sensor_key: str,
        sensor_name: str,
        unit: str | None,
        icon: str,
        state_class: SensorStateClass | None,
        entry_id: str,
    ):
        super().__init__(coordinator)
        self._body = body
        self._sensor_key = sensor_key
        self._attr_name = f"Ephemeris {body.capitalize()} {sensor_name}"
        self._attr_unique_id = f"nasa_astronomy_ephemeris_{body}_{sensor_key}_{entry_id}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_has_entity_name = False

    @property
    def entity_id(self) -> str:
        return f"sensor.nasa_astronomy_ephemeris_{self._body}_{self._sensor_key}"

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        body_data = self.coordinator.data.get(self._body, {})
        value = body_data.get(self._sensor_key)
        if value is None:
            return None
        # Format time values
        if isinstance(value, float) and self._attr_native_unit_of_measurement == "h UTC":
            hours = int(value)
            minutes = int((value - hours) * 60)
            return f"{hours:02d}:{minutes:02d}"
        if isinstance(value, bool):
            return "on" if value else "off"
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "body": self._body,
            "metric": self._sensor_key,
            "provider": "openastronomy_ephemeris",
        }

    @property
    def available(self) -> bool:
        if not self.coordinator.data:
            return False
        return self._body in self.coordinator.data
