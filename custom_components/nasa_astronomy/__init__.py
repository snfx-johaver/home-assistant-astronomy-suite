"""NASA Astronomy Suite - Custom Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NASA Astronomy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api_key = entry.data[CONF_API_KEY]
    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, 3600)

    hass.data[DOMAIN][entry.entry_id] = {
        "session": session,
        "api_key": api_key,
        "update_interval": timedelta(seconds=update_interval),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
