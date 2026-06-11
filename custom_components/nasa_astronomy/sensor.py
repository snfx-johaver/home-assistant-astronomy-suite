"""Sensor platform for NASA Astronomy Suite."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_NEO_LIST
from .coordinator import NasaDataCoordinator

SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="apod",
        name="APOD",
        icon="mdi:image-area",
    ),
    SensorEntityDescription(
        key="neo_count",
        name="NEO Count Today",
        icon="mdi:meteor",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="objects",
    ),
    SensorEntityDescription(
        key="neo_closest",
        name="Closest NEO",
        icon="mdi:bullseye-arrow",
    ),
    SensorEntityDescription(
        key="neo_fastest",
        name="Fastest NEO",
        icon="mdi:speedometer",
    ),
    SensorEntityDescription(
        key="neo_largest",
        name="Largest NEO",
        icon="mdi:resize",
    ),
    SensorEntityDescription(
        key="donki_cme",
        name="Coronal Mass Ejections",
        icon="mdi:white-balance-sunny",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="events",
    ),
    SensorEntityDescription(
        key="donki_flare",
        name="Solar Flares",
        icon="mdi:flare",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="events",
    ),
    SensorEntityDescription(
        key="donki_storm",
        name="Geomagnetic Storms",
        icon="mdi:weather-lightning",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="events",
    ),
    SensorEntityDescription(
        key="eonet_events",
        name="Active Earth Events",
        icon="mdi:earth",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="events",
    ),
    SensorEntityDescription(
        key="techtransfer",
        name="Tech Transfer Patents",
        icon="mdi:rocket-launch",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="patents",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NASA Astronomy sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        NasaAstronomySensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities, True)


class NasaAstronomySensor(CoordinatorEntity[NasaDataCoordinator], SensorEntity):
    """Representation of a NASA Astronomy sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NasaDataCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "NASA Astronomy Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None

        key = self.entity_description.key
        data = self.coordinator.data

        if key == "apod":
            apod = data.get("apod")
            return apod.get("title") if apod else None

        elif key == "neo_count":
            neo = data.get("neo")
            if neo and "element_count" in neo:
                return neo["element_count"]
            return 0

        elif key == "neo_closest":
            neo_obj = self._get_closest_neo()
            if neo_obj:
                dist = neo_obj["close_approach_data"][0]["miss_distance"]["kilometers"]
                return f"{float(dist):,.0f} km"
            return None

        elif key == "neo_fastest":
            neo_obj = self._get_fastest_neo()
            if neo_obj:
                speed = neo_obj["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]
                return f"{float(speed):,.0f} km/h"
            return None

        elif key == "neo_largest":
            neo_obj = self._get_largest_neo()
            if neo_obj:
                diam = neo_obj["estimated_diameter"]["meters"]["estimated_diameter_max"]
                return f"{diam:.0f} m"
            return None

        elif key == "donki_cme":
            cme = data.get("donki_cme")
            return len(cme) if isinstance(cme, list) else 0

        elif key == "donki_flare":
            flr = data.get("donki_flr")
            return len(flr) if isinstance(flr, list) else 0

        elif key == "donki_storm":
            gst = data.get("donki_gst")
            return len(gst) if isinstance(gst, list) else 0

        elif key == "eonet_events":
            eonet = data.get("eonet")
            if eonet and "events" in eonet:
                return len(eonet["events"])
            return 0

        elif key == "techtransfer":
            tt = data.get("techtransfer")
            if tt and "results" in tt:
                return len(tt["results"])
            return 0

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}

        key = self.entity_description.key
        data = self.coordinator.data

        if key == "apod":
            apod = data.get("apod", {})
            if apod:
                return {
                    "title": apod.get("title"),
                    "explanation": apod.get("explanation"),
                    "url": apod.get("url"),
                    "hdurl": apod.get("hdurl"),
                    "date": apod.get("date"),
                    "media_type": apod.get("media_type"),
                    "copyright": apod.get("copyright"),
                }
            return {}

        elif key in ("neo_count", "neo_closest", "neo_fastest", "neo_largest"):
            neo_list = self._get_all_neos()
            hazardous = [n for n in neo_list if n.get("is_potentially_hazardous_asteroid")]
            return {
                "neo_list": [
                    {
                        "name": n.get("name"),
                        "id": n.get("id"),
                        "hazardous": n.get("is_potentially_hazardous_asteroid"),
                        "diameter_min_m": n.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_min"),
                        "diameter_max_m": n.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max"),
                        "velocity_kmh": float(n["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]) if n.get("close_approach_data") else None,
                        "miss_distance_km": float(n["close_approach_data"][0]["miss_distance"]["kilometers"]) if n.get("close_approach_data") else None,
                        "close_approach_date": n["close_approach_data"][0]["close_approach_date_full"] if n.get("close_approach_data") else None,
                    }
                    for n in neo_list
                ],
                "hazardous_count": len(hazardous),
                "total_count": len(neo_list),
            }

        elif key == "donki_cme":
            cme = data.get("donki_cme", [])
            if isinstance(cme, list):
                return {
                    "events": [
                        {
                            "activity_id": e.get("activityID"),
                            "start_time": e.get("startTime"),
                            "type": e.get("type"),
                            "note": e.get("note", "")[:200],
                        }
                        for e in cme[:10]
                    ]
                }
            return {}

        elif key == "donki_flare":
            flr = data.get("donki_flr", [])
            if isinstance(flr, list):
                return {
                    "events": [
                        {
                            "flr_id": e.get("flrID"),
                            "begin_time": e.get("beginTime"),
                            "peak_time": e.get("peakTime"),
                            "end_time": e.get("endTime"),
                            "class_type": e.get("classType"),
                        }
                        for e in flr[:10]
                    ]
                }
            return {}

        elif key == "donki_storm":
            gst = data.get("donki_gst", [])
            if isinstance(gst, list):
                return {
                    "events": [
                        {
                            "gst_id": e.get("gstID"),
                            "start_time": e.get("startTime"),
                            "kp_index": e.get("allKpIndex", [{}])[0].get("kpIndex") if e.get("allKpIndex") else None,
                        }
                        for e in gst[:10]
                    ]
                }
            return {}

        elif key == "eonet_events":
            eonet = data.get("eonet", {})
            if eonet and "events" in eonet:
                return {
                    "events": [
                        {
                            "id": e.get("id"),
                            "title": e.get("title"),
                            "category": e.get("categories", [{}])[0].get("title") if e.get("categories") else None,
                        }
                        for e in eonet["events"][:10]
                    ]
                }
            return {}

        return {}

    def _get_all_neos(self) -> list[dict]:
        """Get all NEOs from today's data."""
        neo = self.coordinator.data.get("neo")
        if not neo or "near_earth_objects" not in neo:
            return []
        all_neos = []
        for date_key, objects in neo["near_earth_objects"].items():
            all_neos.extend(objects)
        return all_neos

    def _get_closest_neo(self) -> dict | None:
        """Get the closest NEO."""
        neos = self._get_all_neos()
        if not neos:
            return None
        return min(
            neos,
            key=lambda n: float(
                n["close_approach_data"][0]["miss_distance"]["kilometers"]
            )
            if n.get("close_approach_data")
            else float("inf"),
        )

    def _get_fastest_neo(self) -> dict | None:
        """Get the fastest NEO."""
        neos = self._get_all_neos()
        if not neos:
            return None
        return max(
            neos,
            key=lambda n: float(
                n["close_approach_data"][0]["relative_velocity"]["kilometers_per_hour"]
            )
            if n.get("close_approach_data")
            else 0,
        )

    def _get_largest_neo(self) -> dict | None:
        """Get the largest NEO."""
        neos = self._get_all_neos()
        if not neos:
            return None
        return max(
            neos,
            key=lambda n: n.get("estimated_diameter", {})
            .get("meters", {})
            .get("estimated_diameter_max", 0),
        )
