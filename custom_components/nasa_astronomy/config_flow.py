"""Config flow for NASA Astronomy Suite."""
from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, APOD_URL

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class NasaAstronomyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NASA Astronomy Suite."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()

            # Check if already configured
            await self.async_set_unique_id(api_key)
            self._abort_if_unique_id_configured()

            # Validate the API key
            valid = await self._test_api_key(api_key)

            if valid is True:
                return self.async_create_entry(
                    title="NASA Astronomy Suite",
                    data={CONF_API_KEY: api_key},
                )
            elif valid is False:
                errors["base"] = "invalid_auth"
            else:
                # None = could not reach API, allow setup anyway
                return self.async_create_entry(
                    title="NASA Astronomy Suite",
                    data={CONF_API_KEY: api_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_api_key(self, api_key: str) -> bool | None:
        """Test if the API key is valid.

        Returns:
            True = valid key (200 response)
            False = invalid key (401/403)
            None = cannot determine (network error, API down)
        """
        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with session.get(
                APOD_URL,
                params={"api_key": api_key},
                timeout=timeout,
            ) as resp:
                if resp.status == 200:
                    return True
                if resp.status in (401, 403):
                    return False
                # Any other status (429, 5xx) — allow setup
                return None
        except Exception:
            # Network error, timeout, etc — allow setup
            return None
