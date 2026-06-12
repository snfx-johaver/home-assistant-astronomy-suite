"""Config flow for Astronomy Space Suite."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_API_KEY
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
