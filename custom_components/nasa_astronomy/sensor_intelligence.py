"""Small automation-facing summaries; detailed series stay bounded attributes."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INTEGRATION_VERSION
from .observing import ObservingCoordinator


class IntelligenceSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name, source=None):
        super().__init__(coordinator)
        self.key = key
        self.source = source
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self.entity_id = f"sensor.astronomy_space_suite_{key}"
        self._attr_icon = "mdi:telescope" if source is None else "mdi:aurora"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)}, "name": "Astronomy Space Suite",
            "manufacturer": "NASA", "model": "Open APIs", "sw_version": INTEGRATION_VERSION,
        }
        if key == "observing_score":
            self._attr_native_unit_of_measurement = "%"
            self._attr_state_class = SensorStateClass.MEASUREMENT

    def _data(self):
        data = self.coordinator.data or {}
        return data.get(self.source) or {} if self.source else data

    @property
    def native_value(self):
        data = self._data()
        if self.key == "space_weather_forecast":
            from datetime import datetime, timezone
            from .providers.forecast import stamp

            forecast = [row for row in data.get("kp") or [] if row["kind"] == "predicted" and stamp(row["time"]) > datetime.now(timezone.utc)]
            return "Elevated" if any(row["kp"] >= 5 for row in forecast) else "Quiet" if forecast else None
        if self.key == "observing_score":
            return data.get("score")
        if self.key == "observing_status":
            return data.get("status") if data.get("score") is not None else None
        return (data.get("best_window") or {}).get("start")

    @property
    def available(self):
        data = self._data()
        return bool(data.get("available")) if self.source else data.get("score") is not None

    @property
    def extra_state_attributes(self):
        data = self._data()
        if self.key in ("observing_score", "space_weather_forecast"):
            return {key: value for key, value in data.items() if key != "score"}
        return {key: data.get(key) for key in ("best_window", "limiting_factor", "stale", "last_success")}


async def async_setup_intelligence(hass, entry, async_add_entities):
    entities = []
    if entry.options.get("observing", {}).get("enabled", False):
        coordinator = ObservingCoordinator(hass, entry)
        await coordinator.async_refresh()
        hass.data[DOMAIN][entry.entry_id]["observing_coordinator"] = coordinator
        for key, title in (
            ("observing_score", "Observing Score"), ("observing_status", "Observing Status"),
            ("best_observing_window", "Best Observing Window"),
        ):
            entities.append(IntelligenceSensor(coordinator, entry, key, title))
    if entry.options.get("space_weather_forecast", {}).get("enabled", False):
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        entities.append(IntelligenceSensor(coordinator, entry, "space_weather_forecast", "Space Weather Forecast", "space_forecast"))
    if entities:
        async_add_entities(entities)
    if entry.options.get("satellites", {}).get("enabled", False):
        from .satellites import SatelliteCoordinator

        coordinator = SatelliteCoordinator(hass, entry)
        await coordinator.async_refresh()
        hass.data[DOMAIN][entry.entry_id]["satellite_coordinator"] = coordinator
        coordinator.nasa.satellite_coordinator = coordinator
        async_add_entities([
            SatelliteSensor(coordinator, entry, ident)
            for ident in coordinator.ids if ident != 25544
        ])


class SatelliteSensor(IntelligenceSensor):
    def __init__(self, coordinator, entry, ident):
        from .satellites import CATALOG

        super().__init__(coordinator, entry, f"satellite_{ident}", CATALOG.get(ident, f"NORAD {ident}"))
        self.ident = str(ident)

    def _data(self):
        return (self.coordinator.data or {}).get(self.ident, {})

    @property
    def native_value(self):
        data = self._data()
        return f"{data['latitude']}, {data['longitude']}" if data else None

    @property
    def available(self):
        return bool(self._data())

    @property
    def extra_state_attributes(self):
        return self._data()
