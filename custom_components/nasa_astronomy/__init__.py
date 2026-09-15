"""Astronomy Space Suite - Custom Integration for Home Assistant."""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import shutil
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_UPDATE_INTERVAL, CONF_ROCKET_API_KEY, INTEGRATION_VERSION
from .coordinator import NasaDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CAMERA]

VERSION = INTEGRATION_VERSION
CARDS_FILENAME = "astronomy-cards.js"
DEEPSKY_CARDS_FILENAME = "deepsky-cards.js"
WORLD_MAP_FILENAME = "world-map.png"

DEPLOYED_FILENAMES: tuple[str, ...] = (
    CARDS_FILENAME,
    WORLD_MAP_FILENAME,
    DEEPSKY_CARDS_FILENAME,
)
BUNDLE_FILENAMES: tuple[str, ...] = tuple(
    filename for filename in DEPLOYED_FILENAMES if filename.endswith(".js")
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


def _lovelace_resources(lovelace_data: object) -> object | None:
    """Return the Lovelace resource collection for current and older HA."""
    resources = getattr(lovelace_data, "resources", None)
    if resources is not None:
        return resources
    if isinstance(lovelace_data, Mapping):
        return lovelace_data.get("resources")
    return None


def deployed_dir(hass: HomeAssistant) -> Path:
    """Return the directory whose files are served below /local/."""
    return Path(hass.config.path("www")) / "community" / "astronomy-cards"


def _cache_bust_for(path: Path) -> str:
    """Build a cache key from the release and the bytes actually served."""
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return f"{VERSION}-unreadable"
    return f"{VERSION}-{digest}"


def resource_url(hass: HomeAssistant, filename: str) -> str:
    """Return the resource URL for one deployed card bundle."""
    served = deployed_dir(hass) / filename
    relative = served.relative_to(Path(hass.config.path("www")))
    return f"/local/{relative.as_posix()}?v={_cache_bust_for(served)}"


def _resource_is_bundle(url: str, filename: str) -> bool:
    """Return whether a resource points at this integration's exact bundle."""
    expected_path = f"/local/community/astronomy-cards/{filename}"
    return urlsplit(url).path == expected_path


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
    await _async_register_deepsky_cards_resource(hass)

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
    """Copy every browser-facing file to the directory served by HA."""
    www_dir = deployed_dir(hass)
    www_dir.mkdir(parents=True, exist_ok=True)

    for filename in DEPLOYED_FILENAMES:
        source = Path(__file__).parent / filename
        if not source.is_file():
            _LOGGER.warning("%s not found: %s", filename, source)
            continue
        dest = www_dir / filename
        shutil.copy2(str(source), str(dest))
        _LOGGER.info("Deployed %s to %s", filename, dest)


async def _async_ensure_resources_loaded(resources: object) -> None:
    """Load HA's lazy resource collection before inspecting its items."""
    get_info = getattr(resources, "async_get_info", None)
    if get_info is None:
        return
    result = get_info()
    if inspect.isawaitable(result):
        await result


async def _async_migrate_bundle_resource(
    hass: HomeAssistant, filename: str, storage_registrar
) -> None:
    """Create, update, and de-duplicate one owned Lovelace resource."""
    wanted_url = await hass.async_add_executor_job(resource_url, hass, filename)
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is not None:
            resources = _lovelace_resources(lovelace_data)
            if resources is not None:
                await _async_ensure_resources_loaded(resources)
                matches = [
                    resource
                    for resource in resources.async_items()
                    if _resource_is_bundle(resource.get("url", ""), filename)
                ]
                if not matches:
                    await resources.async_create_item(
                        {"res_type": "module", "url": wanted_url}
                    )
                    _LOGGER.info("Registered Lovelace resource: %s", wanted_url)
                    return

                primary = matches[0]
                updates = {}
                if primary.get("url") != wanted_url:
                    updates["url"] = wanted_url
                if primary.get("type") != "module":
                    updates["res_type"] = "module"
                if updates:
                    await resources.async_update_item(primary["id"], updates)
                    _LOGGER.info(
                        "Updated Lovelace resource %s to: %s",
                        primary["id"],
                        wanted_url,
                    )

                for duplicate in matches[1:]:
                    await resources.async_delete_item(duplicate["id"])
                if len(matches) > 1:
                    _LOGGER.warning(
                        "Removed %d duplicate Lovelace resource(s) for %s; "
                        "preserved resource id %s",
                        len(matches) - 1,
                        filename,
                        primary["id"],
                    )
                return
    except Exception as err:
        _LOGGER.warning(
            "Lovelace API registration failed for %s (%s: %s); falling back "
            "to .storage/lovelace_resources",
            filename,
            type(err).__name__,
            err,
        )

    await hass.async_add_executor_job(storage_registrar, hass)


async def _async_register_cards_resource(hass: HomeAssistant) -> None:
    """Register or update astronomy-cards.js as a Lovelace resource with cache-bust version."""
    await _async_migrate_bundle_resource(
        hass, CARDS_FILENAME, _register_resource_via_storage
    )


def _migrate_bundle_in_storage(
    hass: HomeAssistant, filename: str, resource_id: str, create_file: bool
) -> None:
    """Fallback migration for installations without the Lovelace API."""
    storage_path = Path(hass.config.path(".storage")) / "lovelace_resources"
    wanted_url = resource_url(hass, filename)
    if not storage_path.is_file():
        if not create_file:
            return
        content = {
            "version": 1,
            "minor_version": 1,
            "key": "lovelace_resources",
            "data": {"items": []},
        }
        storage_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        content = json.loads(storage_path.read_text(encoding="utf-8"))

    items = content.setdefault("data", {}).setdefault("items", [])
    matches = [
        item
        for item in items
        if _resource_is_bundle(item.get("url", ""), filename)
    ]
    changed = False
    if matches:
        primary = matches[0]
        if primary.get("url") != wanted_url:
            primary["url"] = wanted_url
            changed = True
        if primary.get("type") != "module":
            primary["type"] = "module"
            changed = True
        duplicate_ids = {id(item) for item in matches[1:]}
        if duplicate_ids:
            items[:] = [item for item in items if id(item) not in duplicate_ids]
            changed = True
            _LOGGER.warning(
                "Removed %d duplicate stored resource(s) for %s; preserved "
                "resource id %s",
                len(duplicate_ids),
                filename,
                primary.get("id", "<missing>"),
            )
    else:
        items.append({"url": wanted_url, "type": "module", "id": resource_id})
        changed = True

    if changed:
        storage_path.write_text(
            json.dumps(content, indent=2) + "\n", encoding="utf-8"
        )


def _register_resource_via_storage(hass: HomeAssistant) -> None:
    """Fallback: register or update resource by editing .storage/lovelace_resources."""
    _migrate_bundle_in_storage(
        hass,
        CARDS_FILENAME,
        "astronomy_space_suite_cards",
        create_file=True,
    )


async def _async_register_deepsky_cards_resource(hass: HomeAssistant) -> None:
    """Register deepsky-cards.js as a Lovelace resource."""
    await _async_migrate_bundle_resource(
        hass, DEEPSKY_CARDS_FILENAME, _register_deepsky_resource_via_storage
    )


def _register_deepsky_resource_via_storage(hass: HomeAssistant) -> None:
    """Fallback: register deepsky-cards.js resource via .storage/lovelace_resources."""
    _migrate_bundle_in_storage(
        hass,
        DEEPSKY_CARDS_FILENAME,
        "astronomy_space_suite_deepsky_cards",
        create_file=False,
    )
