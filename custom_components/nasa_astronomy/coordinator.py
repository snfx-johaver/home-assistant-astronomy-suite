"""NASA API coordinator for data fetching."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    APOD_URL,
    NEOWS_URL,
    DONKI_CME_URL,
    DONKI_FLR_URL,
    DONKI_GST_URL,
    EONET_URL,
    TECHTRANSFER_URL,
)

_LOGGER = logging.getLogger(__name__)

# NASA API: 1,000 requests/hour limit per key.
# We fetch 7 endpoints per cycle. At 10-min intervals = 42 requests/hour (well under limit).
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)


class NasaDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from NASA APIs."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._session = session
        self._api_key = api_key

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all NASA APIs."""
        data: dict[str, Any] = {}

        data["apod"] = await self._fetch_apod()
        data["neo"] = await self._fetch_neo()
        data["donki_cme"] = await self._fetch_donki_cme()
        data["donki_flr"] = await self._fetch_donki_flr()
        data["donki_gst"] = await self._fetch_donki_gst()
        data["eonet"] = await self._fetch_eonet()
        data["techtransfer"] = await self._fetch_techtransfer()

        # Only raise UpdateFailed if ALL endpoints returned nothing
        if all(v is None for v in data.values()):
            raise UpdateFailed(
                "All NASA API endpoints unreachable — will retry next cycle"
            )

        return data

    async def _fetch_json(self, url: str, params: dict | None = None) -> Any:
        """Fetch JSON from a URL with rate-limit awareness."""
        if params is None:
            params = {}
        params["api_key"] = self._api_key

        try:
            async with self._session.get(
                url, params=params, timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                if resp.status == 429:
                    # Rate limited — back off silently
                    _LOGGER.debug("NASA API rate limited on %s", url)
                    return None
                if resp.status in (500, 502, 503, 504):
                    # Server-side issue — silent, will retry next cycle
                    _LOGGER.debug("NASA API temporarily unavailable (%s)", resp.status)
                    return None
                if resp.status in (401, 403):
                    _LOGGER.warning("NASA API key rejected (HTTP %s)", resp.status)
                    return None
                _LOGGER.debug("NASA API unexpected status %s for %s", resp.status, url)
                return None
        except (aiohttp.ClientError, TimeoutError):
            return None

    async def _fetch_apod(self) -> dict[str, Any] | None:
        """Fetch Astronomy Picture of the Day."""
        return await self._fetch_json(APOD_URL)

    async def _fetch_neo(self) -> dict[str, Any] | None:
        """Fetch Near Earth Objects."""
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"start_date": today, "end_date": today}
        return await self._fetch_json(NEOWS_URL, params)

    async def _fetch_donki_cme(self) -> list | None:
        """Fetch Coronal Mass Ejections (last 7 days)."""
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return await self._fetch_json(DONKI_CME_URL, {"startDate": start})

    async def _fetch_donki_flr(self) -> list | None:
        """Fetch Solar Flares (last 7 days)."""
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return await self._fetch_json(DONKI_FLR_URL, {"startDate": start})

    async def _fetch_donki_gst(self) -> list | None:
        """Fetch Geomagnetic Storms (last 30 days)."""
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        return await self._fetch_json(DONKI_GST_URL, {"startDate": start})

    async def _fetch_eonet(self) -> dict[str, Any] | None:
        """Fetch Earth Observatory Natural Event Tracker."""
        # EONET uses its own endpoint without NASA API key
        params = {"limit": "10", "status": "open"}
        try:
            async with self._session.get(
                EONET_URL, params=params, timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except (aiohttp.ClientError, TimeoutError):
            return None

    async def _fetch_techtransfer(self) -> dict[str, Any] | None:
        """Fetch NASA Tech Transfer patents."""
        return await self._fetch_json(TECHTRANSFER_URL, {"engine": "true"})
