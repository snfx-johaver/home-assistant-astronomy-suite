"""NASA API coordinator for data fetching."""
from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from sgp4 import omm
from sgp4.api import Satrec, jday

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
    ISS_POSITION_URL,
    ISS_ORBIT_ELEMENTS_URL,
    ISS_LEGACY_POSITION_URL,
    EPIC_EARTH_URL,
    SWPC_KP_INDEX_URL,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)
ISS_POSITION_MAX_AGE_SECONDS = 120
ISS_POSITION_FUTURE_TOLERANCE_SECONDS = 30
ISS_ORBIT_REFRESH_INTERVAL = timedelta(hours=2)
ISS_ORBIT_RETRY_INTERVAL = timedelta(minutes=15)
ISS_ORBIT_MAX_AGE = timedelta(days=7)
ISS_LAST_KNOWN_MAX_AGE_SECONDS = 30 * 60


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
        self._iss_omm: dict[str, Any] | None = None
        self._iss_omm_epoch: datetime | None = None
        self._iss_omm_refresh_attempted_at: datetime | None = None
        self._iss_omm_last_attempt_succeeded = False

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
            self._fetch_iss_position(),
            self._fetch_epic_earth(),
            self._fetch_swpc_kp_index(),
            return_exceptions=True,
        )

        keys = [
            "apod", "neo", "donki_cme", "donki_flr",
            "donki_gst", "eonet", "techtransfer", "rocket_launches",
            "iss_position", "epic_earth", "swpc_kp_index",
        ]
        data: dict[str, Any] = {}
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                _LOGGER.debug("Failed to fetch %s: %s", key, result)
                result = None
            if key == "iss_position" and result is None:
                previous = getattr(self, "data", None)
                previous_iss = previous.get(key) if isinstance(previous, dict) else None
                previous_timestamp = (
                    previous_iss.get("timestamp")
                    if isinstance(previous_iss, dict)
                    else None
                )
                try:
                    previous_age = time.time() - int(previous_timestamp)
                except (TypeError, ValueError):
                    previous_age = ISS_LAST_KNOWN_MAX_AGE_SECONDS + 1
                if (
                    previous_iss
                    and 0 <= previous_age <= ISS_LAST_KNOWN_MAX_AGE_SECONDS
                ):
                    data[key] = {**previous_iss, "stale": True}
                    continue
            if result is None:
                data[key] = None
            else:
                data[key] = result

        return data

    async def _fetch_json(self, url: str, params: dict | None = None) -> Any:
        """Fetch JSON from a URL with NASA API key."""
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

    async def _fetch_json_noauth(self, url: str, params: dict | None = None) -> Any:
        """Fetch JSON from a URL without API key."""
        try:
            async with self._session.get(
                url, params=params or {}, timeout=DEFAULT_TIMEOUT
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

    async def _fetch_iss_position(self) -> dict[str, Any] | None:
        """Fetch current ISS position with HTTPS and local-orbit fallbacks."""
        primary = await self._fetch_json_noauth(ISS_POSITION_URL)
        normalized = self._normalize_iss_position(primary, "Where The ISS At")
        if normalized:
            await self._refresh_iss_orbit_elements()
            return normalized

        _LOGGER.debug("Where The ISS At did not return a valid current position")
        await self._refresh_iss_orbit_elements()
        propagated = self._propagate_iss_position()
        if propagated:
            return propagated

        legacy = await self._fetch_json_noauth(ISS_LEGACY_POSITION_URL)
        if isinstance(legacy, dict) and legacy.get("message") == "success":
            normalized = self._normalize_iss_position(legacy, "Open Notify")
            if normalized:
                return normalized

        _LOGGER.debug("All ISS position providers failed")
        return None

    @staticmethod
    def _normalize_iss_position(
        payload: Any,
        source: str,
        *,
        now: float | None = None,
    ) -> dict[str, Any] | None:
        """Validate and map a provider response to the existing sensor shape."""
        if not isinstance(payload, dict):
            return None
        position = payload.get("iss_position", payload)
        if not isinstance(position, dict):
            return None
        try:
            latitude = float(position["latitude"])
            longitude = float(position["longitude"])
            timestamp = int(payload["timestamp"])
        except (KeyError, TypeError, ValueError):
            return None
        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            return None
        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            return None
        current = time.time() if now is None else now
        age = current - timestamp
        if (
            age > ISS_POSITION_MAX_AGE_SECONDS
            or age < -ISS_POSITION_FUTURE_TOLERANCE_SECONDS
        ):
            return None
        return {
            "iss_position": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "timestamp": timestamp,
            "source": source,
            "stale": False,
        }

    async def _refresh_iss_orbit_elements(self) -> None:
        """Refresh cached CelesTrak OMM data at its published two-hour cadence."""
        now = datetime.now(timezone.utc)
        retry_interval = (
            ISS_ORBIT_REFRESH_INTERVAL
            if self._iss_omm_last_attempt_succeeded
            else ISS_ORBIT_RETRY_INTERVAL
        )
        if (
            self._iss_omm_refresh_attempted_at is not None
            and now - self._iss_omm_refresh_attempted_at
            < retry_interval
        ):
            return
        self._iss_omm_refresh_attempted_at = now
        self._iss_omm_last_attempt_succeeded = False
        payload = await self._fetch_json_noauth(ISS_ORBIT_ELEMENTS_URL)
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            _LOGGER.debug("CelesTrak did not return ISS orbital elements")
            return
        fields = payload[0]
        try:
            epoch = datetime.fromisoformat(str(fields["EPOCH"]).replace("Z", "+00:00"))
            if epoch.tzinfo is None:
                epoch = epoch.replace(tzinfo=timezone.utc)
            if now - epoch > ISS_ORBIT_MAX_AGE:
                _LOGGER.debug("CelesTrak ISS orbital elements are too old: %s", epoch)
                return
            satellite = Satrec()
            omm.initialize(satellite, fields)
        except (KeyError, TypeError, ValueError, OverflowError):
            _LOGGER.debug("CelesTrak returned invalid ISS orbital elements")
            return
        self._iss_omm = dict(fields)
        self._iss_omm_epoch = epoch
        self._iss_omm_last_attempt_succeeded = True

    def _propagate_iss_position(
        self,
        at: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Propagate cached ISS orbital elements to a current ground position."""
        if self._iss_omm is None or self._iss_omm_epoch is None:
            return None
        current = at or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        current = current.astimezone(timezone.utc)
        if current - self._iss_omm_epoch > ISS_ORBIT_MAX_AGE:
            _LOGGER.debug(
                "Cached CelesTrak ISS orbital elements are too old: %s",
                self._iss_omm_epoch,
            )
            return None
        try:
            satellite = Satrec()
            omm.initialize(satellite, self._iss_omm)
            jd, fraction = jday(
                current.year,
                current.month,
                current.day,
                current.hour,
                current.minute,
                current.second + current.microsecond / 1_000_000,
            )
            error, position, _velocity = satellite.sgp4(jd, fraction)
            if error:
                _LOGGER.debug("SGP4 could not propagate ISS position: error %s", error)
                return None
            latitude, longitude = self._teme_to_geodetic(position, jd + fraction)
        except (KeyError, TypeError, ValueError, OverflowError):
            _LOGGER.debug("Cached ISS orbital elements could not be propagated")
            return None
        return {
            "iss_position": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "timestamp": int(current.timestamp()),
            "source": "CelesTrak (local SGP4)",
            "stale": False,
        }

    @staticmethod
    def _teme_to_geodetic(
        position_km: tuple[float, float, float],
        julian_date: float,
    ) -> tuple[float, float]:
        """Convert an SGP4 TEME position to WGS84 latitude and longitude."""
        centuries = (julian_date - 2451545.0) / 36525.0
        sidereal_seconds = (
            67310.54841
            + (876600 * 3600 + 8640184.812866) * centuries
            + 0.093104 * centuries**2
            - 0.0000062 * centuries**3
        )
        sidereal = math.radians((sidereal_seconds / 240.0) % 360.0)
        x_teme, y_teme, z = position_km
        x = math.cos(sidereal) * x_teme + math.sin(sidereal) * y_teme
        y = -math.sin(sidereal) * x_teme + math.cos(sidereal) * y_teme

        semi_major = 6378.137
        eccentricity_sq = 6.69437999014e-3
        radius = math.hypot(x, y)
        latitude = math.atan2(z, radius * (1 - eccentricity_sq))
        for _ in range(6):
            prime_vertical = semi_major / math.sqrt(
                1 - eccentricity_sq * math.sin(latitude) ** 2
            )
            latitude = math.atan2(
                z + eccentricity_sq * prime_vertical * math.sin(latitude),
                radius,
            )
        return math.degrees(latitude), math.degrees(math.atan2(y, x))

    async def _fetch_epic_earth(self) -> list | None:
        """Fetch NASA EPIC natural color Earth images metadata."""
        return await self._fetch_json_noauth(EPIC_EARTH_URL)

    async def _fetch_swpc_kp_index(self) -> list | None:
        """Fetch NOAA SWPC planetary K-index (1-minute)."""
        return await self._fetch_json_noauth(SWPC_KP_INDEX_URL)
