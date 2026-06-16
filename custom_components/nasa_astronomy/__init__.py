"""Astronomy Space Suite - Custom Integration for Home Assistant."""
from __future__ import annotations

import logging
import shutil
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_UPDATE_INTERVAL, CONF_ROCKET_API_KEY
from .coordinator import NasaDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]

VERSION = "1.8.1"
CARDS_FILENAME = "astronomy-cards.js"
CARDS_LOCAL_URL = f"/local/community/astronomy-cards/astronomy-cards.js?v={VERSION}"
DEEPSKY_CARDS_FILENAME = "deepsky-cards.js"
DEEPSKY_CARDS_LOCAL_URL = (
    f"/local/community/astronomy-cards/deepsky-cards.js?v={VERSION}"
)

# (filename, lovelace url, storage id) for every bundled card module. The
# filename doubles as the unique match token when reconciling existing
# resources: it is present in each url and avoids the directory-name collision
# between "astronomy-cards.js" and "deepsky-cards.js".
CARDS_RESOURCES = [
    (CARDS_FILENAME, CARDS_LOCAL_URL, "astronomy_space_suite_cards"),
    (
        DEEPSKY_CARDS_FILENAME,
        DEEPSKY_CARDS_LOCAL_URL,
        "astronomy_space_suite_deepsky_cards",
    ),
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Astronomy Space Suite component."""
    # Copy JS cards to www/ so they're served at /local/community/astronomy-cards/
    await hass.async_add_executor_job(_deploy_cards_to_www, hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Astronomy Space Suite from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Deploy cards to www/ and register as Lovelace resource
    await hass.async_add_executor_job(_deploy_cards_to_www, hass)
    await _async_register_cards_resource(hass)

    session = async_get_clientsession(hass)
    api_key = entry.data[CONF_API_KEY]
    rocket_api_key = entry.data.get(CONF_ROCKET_API_KEY, "")
    update_interval = timedelta(
        seconds=entry.options.get(CONF_UPDATE_INTERVAL, 600)
    )

    coordinator = NasaDataCoordinator(
        hass, session, api_key, rocket_api_key, update_interval
    )

    # Don't block setup — refresh in background
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "nasa_astronomy_first_refresh"
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates to reload integration
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — reload integration to apply ephemeris changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


def _deploy_cards_to_www(hass: HomeAssistant) -> None:
    """Copy bundled cards + world-map.png to config/www/community/astronomy-cards/."""
    www_dir = Path(hass.config.path("www")) / "community" / "astronomy-cards"
    www_dir.mkdir(parents=True, exist_ok=True)

    # Deploy JS bundles
    for filename in (CARDS_FILENAME, DEEPSKY_CARDS_FILENAME):
        source = Path(__file__).parent / filename
        if source.is_file():
            dest = www_dir / filename
            shutil.copy2(str(source), str(dest))
            _LOGGER.info("Deployed %s to %s", filename, dest)
        else:
            _LOGGER.warning("Cards JS source not found: %s", source)

    # Deploy world map image
    map_source = Path(__file__).parent / "world-map.png"
    if map_source.is_file():
        map_dest = www_dir / "world-map.png"
        shutil.copy2(str(map_source), str(map_dest))
        _LOGGER.info("Deployed world-map.png to %s", map_dest)
    else:
        _LOGGER.warning("world-map.png not found: %s", map_source)


async def _async_register_cards_resource(hass: HomeAssistant) -> None:
    """Register/update each bundled card module as a Lovelace resource (cache-busted)."""
    # First try the HA API approach
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is not None:
            resources = lovelace_data.get("resources")
            if resources is not None:
                existing = list(resources.async_items())
                for filename, target_url, _rid in CARDS_RESOURCES:
                    match = next(
                        (r for r in existing if filename in r.get("url", "")),
                        None,
                    )
                    if match is None:
                        await resources.async_create_item(
                            {"res_type": "module", "url": target_url}
                        )
                        _LOGGER.info(
                            "Registered Lovelace resource via API: %s", target_url
                        )
                    elif match.get("url") != target_url:
                        await resources.async_update_item(
                            match["id"],
                            {"url": target_url, "res_type": "module"},
                        )
                        _LOGGER.info(
                            "Updated Lovelace resource URL to: %s", target_url
                        )
                return
    except Exception as err:
        _LOGGER.debug("API resource registration failed: %s", err)

    # Fallback: directly update .storage/lovelace_resources
    await hass.async_add_executor_job(_register_resource_via_storage, hass)


def _register_resource_via_storage(hass: HomeAssistant) -> None:
    """Fallback: register/update resources by editing .storage/lovelace_resources."""
    import json

    storage_path = Path(hass.config.path(".storage")) / "lovelace_resources"
    if not storage_path.is_file():
        # Create the storage file with all bundled resources
        data = {
            "version": 1,
            "minor_version": 1,
            "key": "lovelace_resources",
            "data": {
                "items": [
                    {"url": url, "type": "module", "id": rid}
                    for _fn, url, rid in CARDS_RESOURCES
                ]
            },
        }
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(json.dumps(data, indent=2))
        _LOGGER.info("Created lovelace_resources with bundled card modules")
        return

    content = json.loads(storage_path.read_text())
    items = content.get("data", {}).get("items", [])
    changed = False

    for filename, url, rid in CARDS_RESOURCES:
        match = next((it for it in items if filename in it.get("url", "")), None)
        if match is None:
            items.append({"url": url, "type": "module", "id": rid})
            changed = True
            _LOGGER.info("Registered Lovelace resource via storage: %s", url)
        elif match["url"] != url:
            match["url"] = url
            changed = True
            _LOGGER.info("Updated Lovelace resource URL in storage: %s", url)

    if changed:
        content["data"]["items"] = items
        storage_path.write_text(json.dumps(content, indent=2))
