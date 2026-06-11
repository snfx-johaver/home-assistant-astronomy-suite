"""NASA API coordinator for data fetching."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    APOD_URL,
    NEOWS_URL,
    DONKI_CME_URL,
    DONKI_FLR_URL,
    DONKI_GST_URL,
    EONET_URL,
    TECHTRANSFER_URL,
    ROCKET_LAUNCH_URL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)


class NasaDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from NASA APIs."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        rocket_api_key: str,
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
        self._rocket_api_key = rocket_api_key

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all APIs concurrently."""
        results = await asyncio.gather(
            self._fetch_apod(),
            self._fetch_neo(),
            self._fetch_donki_cme(),
            self._fetch_donki_flr(),
            self._fetch_donki_gst(),
            self._fetch_eonet(),
            self._fetch_techtransfer(),
            self._fetch_rocket_launches(),
            return_exceptions=True,
        )

        keys = [
            "apod", "neo", "donki_cme", "donki_flr",
            "donki_gst", "eonet", "techtransfer", "rocket_launches",
        ]
        data: dict[str, Any] = {}
        for key, result in zip(keys, results):
            data[key] = None if isinstance(result, Exception) else result

        return data

    async def _fetch_json(self, url: str, params: dict | None = None) -> Any:
        """Fetch JSON from a URL."""
        if params is None:
            params = {}
        params["api_key"] = self._api_key

        try:
            async with self._session.get(
                url, params=params, timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
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
        params = {"limit": "10", "status": "open"}
        try:
            async with self._session.get(
                EONET_URL, params=params, timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None

    async def _fetch_techtransfer(self) -> dict[str, Any] | None:
        """Fetch NASA Tech Transfer patents."""
        return await self._fetch_json(TECHTRANSFER_URL, {"engine": "true"})

    async def _fetch_rocket_launches(self) -> list | None:
        """Fetch next 5 rocket launches from RocketLaunch.Live."""
        params = {}
        if self._rocket_api_key:
            params["key"] = self._rocket_api_key

        try:
            async with self._session.get(
                ROCKET_LAUNCH_URL, params=params, timeout=DEFAULT_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("result", [])
                return None
        except Exception:
            return None
