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

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_ROCKET_API_KEY, default=""): str,
    }
)


class NasaAstronomyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Astronomy Space Suite."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return AstronomyOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            nasa_key = user_input[CONF_API_KEY].strip()
            rocket_key = user_input.get(CONF_ROCKET_API_KEY, "").strip()

            # Check if already configured
            await self.async_set_unique_id(nasa_key)
            self._abort_if_unique_id_configured()

            # Validate NASA API key
            valid = await self._test_nasa_key(nasa_key)
            if valid is False:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title="Astronomy Space Suite",
                    data={
                        CONF_API_KEY: nasa_key,
                        CONF_ROCKET_API_KEY: rocket_key,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "nasa_url": "https://api.nasa.gov/",
                "rocket_url": "https://rocketlaunch.live/",
            },
        )

    async def _test_nasa_key(self, api_key: str) -> bool | None:
        """Test if the NASA API key is valid.

        Returns True=valid, False=invalid, None=cannot determine.
        """
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
            menu_options=["ephemeris"],
        )

    async def async_step_ephemeris(self, user_input: dict[str, Any] | None = None):
        """Configure ephemeris provider."""
        current = self._config_entry.options.get("ephemeris", {})

        if user_input is not None:
            ephemeris_config = {
                "enabled": user_input.get("enabled", False),
                "latitude": user_input.get("latitude", self.hass.config.latitude),
                "longitude": user_input.get("longitude", self.hass.config.longitude),
                "elevation": user_input.get("elevation", 0),
                "update_interval": user_input.get("update_interval", 3600),
                "bodies": {
                    "sun": user_input.get("body_sun", False),
                    "moon": user_input.get("body_moon", False),
                    "mercury": user_input.get("body_mercury", False),
                    "venus": user_input.get("body_venus", False),
                    "mars": user_input.get("body_mars", False),
                    "jupiter": user_input.get("body_jupiter", False),
                    "saturn": user_input.get("body_saturn", False),
                    "uranus": user_input.get("body_uranus", False),
                    "neptune": user_input.get("body_neptune", False),
                },
            }
            new_options = {**self._config_entry.options, "ephemeris": ephemeris_config}
            return self.async_create_entry(title="", data=new_options)

        bodies = current.get("bodies", {})
        schema = vol.Schema(
            {
                vol.Optional("enabled", default=current.get("enabled", False)): bool,
                vol.Optional("latitude", default=current.get("latitude", self.hass.config.latitude)): vol.Coerce(float),
                vol.Optional("longitude", default=current.get("longitude", self.hass.config.longitude)): vol.Coerce(float),
                vol.Optional("elevation", default=current.get("elevation", 0)): vol.Coerce(float),
                vol.Optional("update_interval", default=current.get("update_interval", 3600)): vol.All(int, vol.Range(min=300, max=86400)),
                vol.Optional("body_sun", default=bodies.get("sun", False)): bool,
                vol.Optional("body_moon", default=bodies.get("moon", False)): bool,
                vol.Optional("body_mercury", default=bodies.get("mercury", False)): bool,
                vol.Optional("body_venus", default=bodies.get("venus", False)): bool,
                vol.Optional("body_mars", default=bodies.get("mars", False)): bool,
                vol.Optional("body_jupiter", default=bodies.get("jupiter", False)): bool,
                vol.Optional("body_saturn", default=bodies.get("saturn", False)): bool,
                vol.Optional("body_uranus", default=bodies.get("uranus", False)): bool,
                vol.Optional("body_neptune", default=bodies.get("neptune", False)): bool,
            }
        )

        return self.async_show_form(step_id="ephemeris", data_schema=schema)
