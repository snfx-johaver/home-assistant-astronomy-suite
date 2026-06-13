"""Config flow for Astronomy Space Suite."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, APOD_URL, CONF_ROCKET_API_KEY

ALL_BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]


def _ephemeris_schema(current: dict, hass) -> vol.Schema:
    """Build the ephemeris configuration schema."""
    bodies = current.get("bodies", {})
    return vol.Schema(
        {
            vol.Optional("enabled", default=current.get("enabled", True)): bool,
            vol.Optional("latitude", default=current.get("latitude", hass.config.latitude)): vol.Coerce(float),
            vol.Optional("longitude", default=current.get("longitude", hass.config.longitude)): vol.Coerce(float),
            vol.Optional("elevation", default=current.get("elevation", hass.config.elevation or 0)): vol.Coerce(float),
            vol.Optional("update_interval", default=current.get("update_interval", 3600)): vol.All(int, vol.Range(min=300, max=86400)),
            vol.Optional("body_sun", default=bodies.get("sun", True)): bool,
            vol.Optional("body_moon", default=bodies.get("moon", True)): bool,
            vol.Optional("body_mercury", default=bodies.get("mercury", True)): bool,
            vol.Optional("body_venus", default=bodies.get("venus", True)): bool,
            vol.Optional("body_mars", default=bodies.get("mars", True)): bool,
            vol.Optional("body_jupiter", default=bodies.get("jupiter", True)): bool,
            vol.Optional("body_saturn", default=bodies.get("saturn", True)): bool,
            vol.Optional("body_uranus", default=bodies.get("uranus", True)): bool,
            vol.Optional("body_neptune", default=bodies.get("neptune", True)): bool,
        }
    )


def _parse_ephemeris_input(user_input: dict, hass) -> dict:
    """Parse ephemeris form input into config structure."""
    return {
        "enabled": user_input.get("enabled", True),
        "latitude": user_input.get("latitude", hass.config.latitude),
        "longitude": user_input.get("longitude", hass.config.longitude),
        "elevation": user_input.get("elevation", 0),
        "update_interval": user_input.get("update_interval", 3600),
        "bodies": {b: user_input.get(f"body_{b}", True) for b in ALL_BODIES},
    }


class NasaAstronomyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Astronomy Space Suite."""

    VERSION = 2

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AstronomyOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: API Keys."""
        errors: dict[str, str] = {}

        if user_input is not None:
            nasa_key = user_input[CONF_API_KEY].strip()
            rocket_key = user_input.get(CONF_ROCKET_API_KEY, "").strip()

            await self.async_set_unique_id(nasa_key)
            self._abort_if_unique_id_configured()

            valid = await self._test_nasa_key(nasa_key)
            if valid is False:
                errors["base"] = "invalid_auth"
            else:
                self._data = {
                    CONF_API_KEY: nasa_key,
                    CONF_ROCKET_API_KEY: rocket_key,
                }
                return await self.async_step_ephemeris()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(CONF_ROCKET_API_KEY, default=""): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "nasa_url": "https://api.nasa.gov/",
                "rocket_url": "https://rocketlaunch.live/",
            },
        )

    async def async_step_ephemeris(self, user_input: dict[str, Any] | None = None):
        """Step 2: Ephemeris configuration."""
        if user_input is not None:
            ephemeris_config = _parse_ephemeris_input(user_input, self.hass)
            return self.async_create_entry(
                title="Astronomy Space Suite",
                data=self._data,
                options={"ephemeris": ephemeris_config},
            )

        schema = _ephemeris_schema({}, self.hass)
        return self.async_show_form(step_id="ephemeris", data_schema=schema)

    async def _test_nasa_key(self, api_key: str) -> bool | None:
        """Test if the NASA API key is valid."""
        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with session.get(
                APOD_URL, params={"api_key": api_key}, timeout=timeout
            ) as resp:
                if resp.status == 200:
                    return True
                if resp.status in (401, 403):
                    return False
                return None
        except Exception:
            return None


class AstronomyOptionsFlow(OptionsFlow):
    """Handle options for Astronomy Space Suite."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Show the main options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["api_keys", "ephemeris"],
        )

    async def async_step_api_keys(self, user_input: dict[str, Any] | None = None):
        """Configure API keys."""
        if user_input is not None:
            nasa_key = user_input.get(CONF_API_KEY, "").strip()
            rocket_key = user_input.get(CONF_ROCKET_API_KEY, "").strip()
            # Update the config entry data
            self.hass.config_entries.async_update_entry(
                self._config_entry,
                data={
                    **self._config_entry.data,
                    CONF_API_KEY: nasa_key,
                    CONF_ROCKET_API_KEY: rocket_key,
                },
            )
            return self.async_create_entry(title="", data=self._config_entry.options)

        current_nasa = self._config_entry.data.get(CONF_API_KEY, "")
        current_rocket = self._config_entry.data.get(CONF_ROCKET_API_KEY, "")
        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY, default=current_nasa): str,
                vol.Optional(CONF_ROCKET_API_KEY, default=current_rocket): str,
            }
        )
        return self.async_show_form(step_id="api_keys", data_schema=schema)

    async def async_step_ephemeris(self, user_input: dict[str, Any] | None = None):
        """Configure ephemeris provider."""
        current = self._config_entry.options.get("ephemeris", {})

        if user_input is not None:
            ephemeris_config = _parse_ephemeris_input(user_input, self.hass)
            new_options = {**self._config_entry.options, "ephemeris": ephemeris_config}
            return self.async_create_entry(title="", data=new_options)

        schema = _ephemeris_schema(current, self.hass)
        return self.async_show_form(step_id="ephemeris", data_schema=schema)
