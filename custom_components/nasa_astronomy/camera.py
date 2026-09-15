"""Camera platform for Astronomy Space Suite."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    EPIC_IMAGE_BASE_URL,
    GOES16_EARTH_URL,
    GOES18_EARTH_URL,
    HIMAWARI8_EARTH_URL,
    INTEGRATION_VERSION,
    METEOSAT12_EARTH_URL,
    SDO_SUN_URL,
    SOHO_SUN_URL,
)
from .coordinator import NasaDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cameras from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        NasaApodCamera(coordinator, entry),
        NasaEpicEarthCamera(coordinator, entry),
        StaticImageCamera(coordinator, entry, "GOES-16 Earth", "mdi:satellite-variant", GOES16_EARTH_URL, "goes_16_earth", {"source": "NOAA GOES-16", "band": "GeoColor Full Disk", "region": "Americas", "update_frequency": "Every 10 minutes"}),
        StaticImageCamera(coordinator, entry, "GOES-18 Earth", "mdi:satellite-variant", GOES18_EARTH_URL, "goes_18_earth", {"source": "NOAA GOES-18", "band": "GeoColor Full Disk", "region": "Pacific", "update_frequency": "Every 10 minutes"}),
        StaticImageCamera(coordinator, entry, "Himawari-8 Earth", "mdi:satellite-variant", HIMAWARI8_EARTH_URL, "himawari8_earth", {"source": "Himawari-8 (NICT Japan)", "band": "True Color", "region": "Asia/Pacific", "update_frequency": "Every 10 minutes"}),
        Meteosat12EarthCamera(coordinator, entry),
        StaticImageCamera(coordinator, entry, "SDO Sun", "mdi:white-balance-sunny", SDO_SUN_URL, "sdo_sun", {"source": "NASA SDO", "wavelength": "171 Å (Fe IX)", "description": "Solar corona in extreme ultraviolet", "update_frequency": "Near real-time"}),
        StaticImageCamera(coordinator, entry, "SOHO Sun", "mdi:weather-sunny-alert", SOHO_SUN_URL, "soho_sun", {"source": "ESA/NASA SOHO LASCO C3", "description": "Coronagraph showing solar wind and CMEs", "update_frequency": "Every 20 minutes"}),
    ], True)


class NasaApodCamera(CoordinatorEntity[NasaDataCoordinator], Camera):
    """Camera entity showing the Astronomy Picture of the Day."""

    _attr_has_entity_name = True
    _attr_name = "APOD Image"
    _attr_icon = "mdi:image-area"

    def __init__(
        self,
        coordinator: NasaDataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}_apod_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self._image_url: str | None = None
        self._cached_image: bytes | None = None

    @property
    def entity_picture(self) -> str | None:
        """Return the APOD URL as entity picture."""
        if self.coordinator.data and self.coordinator.data.get("apod"):
            apod = self.coordinator.data["apod"]
            if apod.get("media_type") == "image":
                return apod.get("url")
        return None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the APOD image."""
        if not self.coordinator.data or not self.coordinator.data.get("apod"):
            return None

        apod = self.coordinator.data["apod"]
        if apod.get("media_type") != "image":
            return None

        url = apod.get("url")
        if not url:
            return None

        if url == self._image_url and self._cached_image:
            return self._cached_image

        try:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    self._cached_image = await resp.read()
                    self._image_url = url
                    return self._cached_image
        except (aiohttp.ClientError, TimeoutError):
            pass

        return self._cached_image

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return APOD metadata."""
        if not self.coordinator.data or not self.coordinator.data.get("apod"):
            return {}
        apod = self.coordinator.data["apod"]
        return {
            "title": apod.get("title"),
            "explanation": apod.get("explanation"),
            "date": apod.get("date"),
            "hdurl": apod.get("hdurl"),
            "copyright": apod.get("copyright"),
        }


class NasaEpicEarthCamera(CoordinatorEntity[NasaDataCoordinator], Camera):
    """Camera entity showing NASA EPIC full-disk Earth images."""

    _attr_has_entity_name = True
    _attr_name = "EPIC Earth"
    _attr_icon = "mdi:earth"

    def __init__(
        self,
        coordinator: NasaDataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the EPIC Earth camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}_epic_earth_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self._cached_image: bytes | None = None
        self._cached_url: str | None = None

    def _get_latest_image_url(self) -> str | None:
        """Build the URL for the latest EPIC image."""
        if not self.coordinator.data:
            return None
        epic = self.coordinator.data.get("epic_earth")
        if not epic or not isinstance(epic, list) or len(epic) == 0:
            return None
        latest = epic[0]
        image_name = latest.get("image")
        date_str = latest.get("date", "")
        if not image_name or not date_str:
            return None
        # Date format: "2024-01-15 06:24:32" → 2024/01/15
        date_part = date_str.split(" ")[0]
        parts = date_part.split("-")
        if len(parts) != 3:
            return None
        return f"{EPIC_IMAGE_BASE_URL}/{parts[0]}/{parts[1]}/{parts[2]}/png/{image_name}.png"

    @property
    def entity_picture(self) -> str | None:
        """Return the EPIC image URL as entity picture."""
        return self._get_latest_image_url()

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the latest EPIC Earth image."""
        url = self._get_latest_image_url()
        if not url:
            return self._cached_image

        if url == self._cached_url and self._cached_image:
            return self._cached_image

        try:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status == 200:
                    self._cached_image = await resp.read()
                    self._cached_url = url
                    return self._cached_image
        except (aiohttp.ClientError, TimeoutError):
            pass

        return self._cached_image

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return EPIC image metadata."""
        if not self.coordinator.data:
            return {}
        epic = self.coordinator.data.get("epic_earth")
        if not epic or not isinstance(epic, list) or len(epic) == 0:
            return {}
        latest = epic[0]
        return {
            "caption": latest.get("caption", ""),
            "date": latest.get("date", ""),
            "image_url": self._get_latest_image_url() or "",
            "centroid_coordinates": latest.get("centroid_coordinates", {}),
            "total_images_today": len(epic),
        }


class Meteosat12EarthCamera(CoordinatorEntity[NasaDataCoordinator], Camera):
    """Cached EUMETSAT Meteosat-12 GeoColour full-disc camera."""

    _attr_has_entity_name = True
    _attr_name = "Meteosat-12 Earth"
    _attr_icon = "mdi:satellite-variant"

    def __init__(
        self,
        coordinator: NasaDataCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the Meteosat-12 camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{entry.entry_id}_meteosat_12_earth_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self._cached_image: bytes | None = None
        self._refresh_lock = asyncio.Lock()

    async def async_added_to_hass(self) -> None:
        """Start the independent EUMETSAT refresh lifecycle."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_scheduled_refresh,
                timedelta(minutes=10),
            )
        )
        self.hass.async_create_task(
            self._async_refresh(),
            "Meteosat-12 initial image refresh",
        )

    async def _async_scheduled_refresh(self, _now: Any) -> None:
        """Refresh the cached image on the ten-minute source cadence."""
        await self._async_refresh()

    async def _async_refresh(self, *, force: bool = True) -> bytes | None:
        """Download and validate one PNG, retaining the previous good image."""
        async with self._refresh_lock:
            if self._cached_image is not None and not force:
                return self._cached_image
            try:
                session = async_get_clientsession(self.hass)
                timeout = aiohttp.ClientTimeout(total=25)
                async with session.get(METEOSAT12_EARTH_URL, timeout=timeout) as resp:
                    if resp.status != 200:
                        _LOGGER.warning(
                            "Meteosat-12 image refresh failed with HTTP status %s",
                            resp.status,
                        )
                        return self._cached_image

                    content_type = resp.headers.get("Content-Type", "").lower()
                    image = await resp.read()
                    if (
                        not content_type.startswith("image/png")
                        or not image.startswith(b"\x89PNG\r\n\x1a\n")
                    ):
                        _LOGGER.warning(
                            "Meteosat-12 image refresh returned invalid PNG content "
                            "(content type: %s, bytes: %s)",
                            content_type or "missing",
                            len(image),
                        )
                        return self._cached_image

                    self._cached_image = image
                    return image
            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.warning("Meteosat-12 image refresh failed: %s", err)
                return self._cached_image

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Serve cached bytes, fetching synchronously only before the first refresh."""
        if self._cached_image is None:
            return await self._async_refresh(force=False)
        return self._cached_image

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return Meteosat observation metadata."""
        return {
            "source": "EUMETSAT",
            "band": "GeoColour RGB",
            "region": "Europe/Africa",
            "update_frequency": "Every 10 minutes",
            "attribution": "EUMETSAT / NASA",
            "background": "NASA Black Marble",
        }


class StaticImageCamera(CoordinatorEntity[NasaDataCoordinator], Camera):
    """Generic camera entity for any static image URL (GOES, Himawari, SDO, SOHO)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NasaDataCoordinator,
        entry: ConfigEntry,
        name: str,
        icon: str,
        image_url: str,
        uid_suffix: str,
        metadata: dict[str, str],
    ) -> None:
        """Initialize the static image camera."""
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_name = name
        self._attr_icon = icon
        self._image_url = image_url
        self._metadata = metadata
        self._attr_unique_id = f"{entry.entry_id}_{uid_suffix}_camera"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Astronomy Space Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": INTEGRATION_VERSION,
        }
        self._cached_image: bytes | None = None

    @property
    def entity_picture(self) -> str | None:
        """Return the image URL."""
        return self._image_url

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the latest image."""
        try:
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.get(self._image_url, timeout=timeout) as resp:
                if resp.status == 200:
                    self._cached_image = await resp.read()
                    return self._cached_image
        except (aiohttp.ClientError, TimeoutError):
            pass
        return self._cached_image

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return metadata."""
        attrs = dict(self._metadata)
        attrs["image_url"] = self._image_url
        return attrs
