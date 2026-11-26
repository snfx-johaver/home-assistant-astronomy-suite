"""Location-aware eclipse predictions using Astronomy Engine."""
from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Any

import astronomy

HORIZON_MONTHS = 18
MAX_PER_TYPE = 3


def _time(value: datetime) -> astronomy.Time:
    return astronomy.Time.Make(
        value.year, value.month, value.day, value.hour, value.minute,
        value.second + value.microsecond / 1_000_000,
    )


def _utc(value: astronomy.Time) -> datetime:
    return value.Utc().replace(tzinfo=timezone.utc)


class EclipseProvider:
    """Cache future events daily; refresh immediately after an event ends."""

    def __init__(self, latitude: float, longitude: float, elevation: float):
        self.observer = astronomy.Observer(latitude, longitude, elevation)
        self._cache: dict[str, Any] | None = None
        self._expires: datetime | None = None

    def _altitude(self, body: astronomy.Body, time: astronomy.Time) -> float:
        equator = astronomy.Equator(body, time, self.observer, True, True)
        return astronomy.Horizon(
            time, self.observer, equator.ra, equator.dec,
            astronomy.Refraction.Airless,
        ).altitude

    def _visible_window(
        self, body: astronomy.Body, begin: astronomy.Time, end: astronomy.Time,
    ) -> tuple[astronomy.Time, astronomy.Time] | None:
        """Intersect eclipse contacts with the body's geometric horizon."""
        duration = end.ut - begin.ut
        if self._altitude(body, begin) > 0:
            visible_begin = begin
        else:
            visible_begin = astronomy.SearchAltitude(
                body, self.observer, astronomy.Direction.Rise, begin, duration, 0,
            )
            if visible_begin is None:
                return None
        visible_end = astronomy.SearchAltitude(
            body, self.observer, astronomy.Direction.Set,
            visible_begin, end.ut - visible_begin.ut, 0,
        ) or end
        if visible_end.ut <= visible_begin.ut:
            return None
        return visible_begin, visible_end

    def _event(
        self, body: astronomy.Body, kind: astronomy.EclipseKind,
        obscuration: float, peak: astronomy.Time, begin: astronomy.Time,
        end: astronomy.Time, central_begin: astronomy.Time | None,
        central_end: astronomy.Time | None, now: datetime,
    ) -> dict[str, Any] | None:
        if _utc(end) <= now:
            return None
        window = self._visible_window(body, begin, end)
        if window is None or _utc(window[1]) <= now:
            return None
        return {
            "type": "solar" if body == astronomy.Body.Sun else "lunar",
            "kind": kind.name.lower(),
            "peak": _utc(peak).isoformat(),
            "begin": _utc(begin).isoformat(),
            "end": _utc(end).isoformat(),
            "visible_begin": _utc(window[0]).isoformat(),
            "visible_end": _utc(window[1]).isoformat(),
            "peak_visible": self._altitude(body, peak) > 0,
            "obscuration_pct": round(obscuration * 100, 1),
            "duration_minutes": round((end.ut - begin.ut) * 1440, 1),
            "central_begin": _utc(central_begin).isoformat() if central_begin else None,
            "central_end": _utc(central_end).isoformat() if central_end else None,
        }

    def get_eclipses(self, now: datetime | None = None) -> dict[str, Any]:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if self._cache is not None and self._expires is not None and now < self._expires:
            return self._cache

        month_index = now.year * 12 + now.month - 1 + HORIZON_MONTHS
        year, month = divmod(month_index, 12)
        month += 1
        horizon = now.replace(
            year=year, month=month, day=min(now.day, monthrange(year, month)[1]),
        )
        # Include an eclipse already in progress, including one past its peak.
        start = _time(now - timedelta(days=1))
        lunar: list[dict[str, Any]] = []
        eclipse = astronomy.SearchLunarEclipse(start)
        while _utc(eclipse.peak) <= horizon:
            event = self._event(
                astronomy.Body.Moon, eclipse.kind, eclipse.obscuration,
                eclipse.peak,
                eclipse.peak.AddDays(-eclipse.sd_penum / 1440),
                eclipse.peak.AddDays(eclipse.sd_penum / 1440),
                eclipse.peak.AddDays(-eclipse.sd_total / 1440) if eclipse.sd_total else None,
                eclipse.peak.AddDays(eclipse.sd_total / 1440) if eclipse.sd_total else None,
                now,
            )
            if event:
                lunar.append(event)
                if len(lunar) == MAX_PER_TYPE:
                    break
            eclipse = astronomy.NextLunarEclipse(eclipse.peak)

        solar: list[dict[str, Any]] = []
        local = astronomy.SearchLocalSolarEclipse(start, self.observer)
        while _utc(local.peak.time) <= horizon:
            event = self._event(
                astronomy.Body.Sun, local.kind, local.obscuration, local.peak.time,
                local.partial_begin.time, local.partial_end.time,
                local.total_begin.time if local.total_begin else None,
                local.total_end.time if local.total_end else None, now,
            )
            if event:
                solar.append(event)
                if len(solar) == MAX_PER_TYPE:
                    break
            local = astronomy.NextLocalSolarEclipse(local.peak.time, self.observer)

        data = {
            "solar": solar,
            "lunar": lunar,
            "search_start": now.isoformat(),
            "search_end": horizon.isoformat(),
            "horizon_months": HORIZON_MONTHS,
            "max_per_type": MAX_PER_TYPE,
            "latitude": self.observer.latitude,
            "longitude": self.observer.longitude,
            "elevation": self.observer.height,
            "time_zone": "UTC",
            "calculated_at": now.isoformat(),
        }
        expires = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        for event in solar + lunar:
            expires = min(expires, datetime.fromisoformat(event["visible_end"]))
        self._cache = data
        self._expires = expires
        return data
