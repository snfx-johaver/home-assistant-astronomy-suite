"""Validated, coalesced forecast requests with bounded last-success fallback."""
from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import aiohttp

_LOGGER = logging.getLogger(__name__)


def number(value: Any, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError("Missing numeric forecast value")
    result = float(value)
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValueError("Forecast value outside supported range")
    return result


def stamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Missing forecast timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


class ForecastRequest:
    """One in-flight task and a conservative retry cadence per endpoint."""

    def __init__(self, session, label: str, url: str, parser: Callable, interval: timedelta, max_age: timedelta):
        self.session, self.label, self.url, self.parser = session, label, url, parser
        self.interval, self.max_age = interval, max_age
        self.data = None
        self.last_success: datetime | None = None
        self.next_attempt: datetime | None = None
        self.error: str | None = None
        self._task = None

    async def get(self, params: dict | None = None):
        now = datetime.now(timezone.utc)
        if self._task is None and self.next_attempt is not None and now < self.next_attempt:
            return self._usable(now)
        if self._task is None:
            self._task = asyncio.create_task(self._download(params))
        task = self._task
        try:
            return await asyncio.shield(task)
        finally:
            if task.done() and self._task is task:
                self._task = None

    def _usable(self, now: datetime):
        if self.last_success is None or now - self.last_success > self.max_age:
            return None
        return self.data

    async def _download(self, params):
        now = datetime.now(timezone.utc)
        self.next_attempt = now + timedelta(minutes=15)
        try:
            async with self.session.get(self.url, params=params or {}, timeout=aiohttp.ClientTimeout(total=20)) as response:
                if response.status == 429:
                    delay = response.headers.get("Retry-After", "900")
                    try:
                        seconds = max(900, min(86400, int(delay)))
                    except ValueError:
                        seconds = 900
                    self.next_attempt = now + timedelta(seconds=seconds)
                    raise ValueError("Rate limited")
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                parsed = self.parser(await response.json())
            self.data = parsed
            self.last_success = now
            self.next_attempt = now + self.interval
            self.error = None
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError, KeyError) as err:
            # Exception text may contain request URLs/location; retain type only.
            self.error = type(err).__name__
            log = _LOGGER.debug if self._usable(now) is not None else _LOGGER.warning
            log("%s forecast refresh failed (%s); %s", self.label, self.error,
                "cached data retained" if self._usable(now) is not None else "no usable forecast")
        return self._usable(now)

    def diagnostics(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "age_seconds": int((now - self.last_success).total_seconds()) if self.last_success else None,
            "stale": self.error is not None, "last_error_type": self.error,
            "usable": self._usable(now) is not None,
        }


WEATHER_FIELDS = {
    "cloud_cover": (0, 100), "cloud_cover_low": (0, 100),
    "cloud_cover_mid": (0, 100), "cloud_cover_high": (0, 100),
    "relative_humidity_2m": (0, 100), "precipitation_probability": (0, 100),
    "temperature_2m": (-100, 70), "dew_point_2m": (-100, 70),
    "wind_speed_10m": (0, 150), "wind_gusts_10m": (0, 150),
    "visibility": (0, 200000),
}


def parse_weather(payload: Any) -> list[dict]:
    hourly = payload["hourly"]
    times = hourly["time"]
    if not isinstance(times, list) or not 24 <= len(times) <= 168:
        raise ValueError("Incomplete hourly weather forecast")
    if any(not isinstance(hourly.get(key), list) or len(hourly[key]) != len(times) for key in WEATHER_FIELDS):
        raise ValueError("Mismatched forecast series")
    rows = []
    previous = None
    for index, value in enumerate(times):
        at = datetime.fromtimestamp(number(value, 0, 4102444800), timezone.utc)
        if previous is not None and at - previous != timedelta(hours=1):
            raise ValueError("Non-hourly forecast")
        previous = at
        row = {"time": at.isoformat()}
        # A missing hour remains explicitly unknown rather than rejecting all
        # useful hours or manufacturing ideal conditions.
        for key, bounds in WEATHER_FIELDS.items():
            raw = hourly[key][index]
            row[key] = number(raw, *bounds) if raw is not None else None
        rows.append(row)
    return rows
