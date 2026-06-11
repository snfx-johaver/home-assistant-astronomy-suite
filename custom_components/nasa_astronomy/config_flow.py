"""Config flow for NASA Astronomy Suite."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, APOD_URL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class NasaAstronomyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NASA Astronomy Suite."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            session = async_get_clientsession(self.hass)
            timeout = aiohttp.ClientTimeout(total=30)

            try:
                async with session.get(
                    APOD_URL,
                    params={"api_key": api_key},
                    timeout=timeout,
                ) as resp:
                    if resp.status == 200:
                        await self._async_abort_entries_match(
                            {CONF_API_KEY: api_key}
                        )
                        return self.async_create_entry(
                            title="NASA Astronomy Suite",
                            data={CONF_API_KEY: api_key},
                        )
                    elif resp.status in (401, 403):
                        errors["base"] = "invalid_auth"
                    elif resp.status == 503:
                        # NASA API is temporarily down — allow setup anyway
                        _LOGGER.warning(
                            "NASA API returned 503 (unavailable). "
                            "Allowing setup — data will sync when API recovers."
                        )
                        return self.async_create_entry(
                            title="NASA Astronomy Suite",
                            data={CONF_API_KEY: api_key},
                        )
                    else:
                        _LOGGER.error(
                            "NASA API returned status %s: %s",
                            resp.status,
                            await resp.text(),
                        )
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error to NASA API: %s", err)
                errors["base"] = "cannot_connect"
            except TimeoutError:
                _LOGGER.error("Timeout connecting to NASA API")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
