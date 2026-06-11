"""NASA Astronomy Suite - Custom Integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.lovelace.resources import (
    ResourceStorageCollection,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_UPDATE_INTERVAL
from .coordinator import NasaDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]

CARDS_URL = f"/{DOMAIN}/astronomy-cards.js"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the NASA Astronomy Suite component."""
    # Register static path for the bundled JS cards
    hass.http.register_static_path(
        CARDS_URL,
        str(Path(__file__).parent / "astronomy-cards.js"),
        cache_headers=True,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NASA Astronomy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Auto-register the cards JS as a Lovelace resource
    await _async_register_cards_resource(hass)

    session = async_get_clientsession(hass)
    api_key = entry.data[CONF_API_KEY]
    update_interval = timedelta(
        seconds=entry.options.get(CONF_UPDATE_INTERVAL, 600)
    )

    coordinator = NasaDataCoordinator(hass, session, api_key, update_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_register_cards_resource(hass: HomeAssistant) -> None:
    """Register astronomy-cards.js as a Lovelace resource if not already present."""
    try:
        resources: ResourceStorageCollection = hass.data["lovelace"]["resources"]

        # Check if already registered
        if resources.async_items():
            for resource in resources.async_items():
                if CARDS_URL in resource.get("url", ""):
                    return

        # Add the resource
        await resources.async_create_item(
            {"res_type": "module", "url": CARDS_URL}
        )
        _LOGGER.debug("Registered astronomy-cards.js as Lovelace resource")
    except Exception:
        # Fallback: if lovelace resources API isn't available (YAML mode),
        # the user must add the resource manually
        _LOGGER.debug(
            "Could not auto-register Lovelace resource. "
            "If using YAML mode, add to configuration.yaml: "
            "lovelace.resources: [{url: '%s', type: module}]",
            CARDS_URL,
        )
