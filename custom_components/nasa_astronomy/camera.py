"""Camera platform for NASA Astronomy Suite - APOD image."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import NasaDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NASA APOD camera from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([NasaApodCamera(coordinator, entry)], True)


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
            "name": "NASA Astronomy Suite",
            "manufacturer": "NASA",
            "model": "Open APIs",
            "sw_version": "1.0.0",
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
