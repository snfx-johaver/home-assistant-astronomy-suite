"""Bounded local event and lunar intelligence; no additional ephemeris engine."""
from __future__ import annotations

import math
from calendar import monthrange
from datetime import datetime, timedelta, timezone
from typing import Any

import astronomy

from .eclipses import HORIZON_MONTHS, _time, _utc

MAX_EVENTS = 48
AU_KM = 149597870.7
# Nominal annual solar-longitude peaks and ideal zenithal hourly rates, IMO
# Working List. These are calendar estimates, not predictions of outbursts.
SHOWERS = (
    ("Quadrantids", 283.16, 230.0, 49.0, 80),
    ("Lyrids", 32.32, 271.0, 34.0, 18),
    ("Eta Aquariids", 45.5, 338.0, -1.0, 50),
    ("Southern Delta Aquariids", 125.0, 340.0, -16.0, 25),
    ("Perseids", 140.0, 48.0, 58.0, 100),
    ("Orionids", 208.0, 95.0, 16.0, 20),
    ("Leonids", 235.27, 152.0, 22.0, 15),
    ("Geminids", 262.2, 112.0, 33.0, 150),
    ("Ursids", 270.7, 217.0, 76.0, 10),
)


def utc_now(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        raise ValueError("A timezone-aware observation time is required")
    return value.astimezone(timezone.utc)


def horizon_at(observer: astronomy.Observer, body: astronomy.Body, at: datetime) -> dict[str, float]:
    time = _time(at)
    equator = astronomy.Equator(body, time, observer, True, True)
    horizon = astronomy.Horizon(time, observer, equator.ra, equator.dec, astronomy.Refraction.Airless)
    return {"altitude": round(horizon.altitude, 1), "azimuth": round(horizon.azimuth, 1)}


def lunar_details(observer: astronomy.Observer, at: datetime) -> dict[str, Any]:
    at = utc_now(at)
    time = _time(at)
    previous_new = astronomy.SearchMoonPhase(0, time, -35)
    distance = astronomy.GeoMoon(time).Length() * AU_KM
    phase = astronomy.MoonPhase(time)
    illumination = astronomy.Illumination(astronomy.Body.Moon, time).phase_fraction
    phases = []
    for angle, name in ((0, "New Moon"), (90, "First quarter"), (180, "Full Moon"), (270, "Last quarter")):
        result = astronomy.SearchMoonPhase(angle, time, 35)
        if result is not None:
            phases.append({"title": name, "angle": angle, "time": _utc(result).isoformat()})
    phases.sort(key=lambda item: item["time"])
    apsis = astronomy.SearchLunarApsis(time)
    apsides = {}
    for _ in range(2):
        name = "perigee" if apsis.kind == astronomy.ApsisKind.Pericenter else "apogee"
        apsides[name] = {"time": _utc(apsis.time).isoformat(), "distance_km": round(apsis.dist_km)}
        apsis = astronomy.NextLunarApsis(apsis)
    rise = astronomy.SearchRiseSet(astronomy.Body.Moon, observer, astronomy.Direction.Rise, time, 2)
    setting = astronomy.SearchRiseSet(astronomy.Body.Moon, observer, astronomy.Direction.Set, time, 2)
    transit = astronomy.SearchHourAngle(astronomy.Body.Moon, observer, 0, time)
    position = horizon_at(observer, astronomy.Body.Moon, at)
    return {
        "age_days": round((at - _utc(previous_new)).total_seconds() / 86400, 1) if previous_new else None,
        "distance_km": round(distance),
        "angular_diameter_arcmin": round(math.degrees(2 * math.asin(1737.4 / distance)) * 60, 2),
        "phase_longitude": round(phase, 2),
        "illumination_pct": round(illumination * 100),
        "phases": phases,
        **apsides,
        "rise_time": _utc(rise).isoformat() if rise else None,
        "transit_time": _utc(transit.time).isoformat(),
        "transit_altitude": round(transit.hor.altitude, 1),
        "set_time": _utc(setting).isoformat() if setting else None,
        "moonlight_impact": round(illumination * max(0, math.sin(math.radians(position["altitude"]))) * 100),
        "sky_path": [
            {"time": (at + timedelta(hours=hour)).isoformat(),
             **horizon_at(observer, astronomy.Body.Moon, at + timedelta(hours=hour))}
            for hour in range(25)
        ],
        **position,
        "calculation_method": "Astronomy Engine",
        "calculated_at": at.isoformat(),
    }


class CelestialEventsProvider:
    """Daily 18-month predictions, sharing the existing eclipse result."""

    def __init__(self, latitude: float, longitude: float, elevation: float):
        self.observer = astronomy.Observer(latitude, longitude, elevation)
        self._events: list[dict[str, Any]] | None = None
        self._expires: datetime | None = None
        self._horizon: datetime | None = None

    def _event(
        self, kind: str, title: str, peak: datetime, body: astronomy.Body | None = None,
        *, duration: timedelta = timedelta(hours=12), **extra: Any,
    ) -> dict[str, Any]:
        position = horizon_at(self.observer, body, peak) if body else {}
        dark = horizon_at(self.observer, astronomy.Body.Sun, peak)["altitude"] < -12
        return {
            "event_type": kind, "title": title,
            "start": (peak - duration).isoformat(), "peak": peak.isoformat(),
            "end": (peak + duration).isoformat(),
            "visibility_from_location": (
                "above_horizon_in_darkness" if position.get("altitude", -90) > 0 and dark
                else "below_horizon_or_daylight" if body else "global_event"
            ),
            "altitude_at_peak": position.get("altitude"),
            "azimuth_at_peak": position.get("azimuth"),
            "significance": "seasonal" if kind == "season" else "observing",
            "calculation_method": "Astronomy Engine",
            **extra,
        }

    def _calculate(self, now: datetime) -> list[dict[str, Any]]:
        index = now.year * 12 + now.month - 1 + HORIZON_MONTHS
        year, month = divmod(index, 12)
        self._horizon = now.replace(year=year, month=month + 1, day=min(now.day, monthrange(year, month + 1)[1]))
        begin = now - timedelta(days=1)
        events = []
        for year in range(begin.year, self._horizon.year + 1):
            seasons = astronomy.Seasons(year)
            for key, title in (
                ("mar_equinox", "March equinox"), ("jun_solstice", "June solstice"),
                ("sep_equinox", "September equinox"), ("dec_solstice", "December solstice"),
            ):
                events.append(self._event("season", title, _utc(getattr(seasons, key))))
            for title, longitude, ra, dec, rate in SHOWERS:
                peak = astronomy.SearchSunLongitude(longitude, _time(datetime(year, 1, 1, tzinfo=timezone.utc)), 370)
                if peak is None:
                    continue
                at = _utc(peak)
                radiant = astronomy.Horizon(peak, self.observer, ra / 15, dec, astronomy.Refraction.Airless)
                moon = astronomy.Illumination(astronomy.Body.Moon, peak).phase_fraction
                viewing = []
                for hour in range(-24, 25):
                    moment = at + timedelta(hours=hour)
                    t = _time(moment)
                    local_radiant = astronomy.Horizon(t, self.observer, ra / 15, dec, astronomy.Refraction.Airless)
                    if local_radiant.altitude <= 0 or horizon_at(self.observer, astronomy.Body.Sun, moment)["altitude"] >= -12:
                        continue
                    moon_altitude = horizon_at(self.observer, astronomy.Body.Moon, moment)["altitude"]
                    interference = astronomy.Illumination(astronomy.Body.Moon, t).phase_fraction * max(0, math.sin(math.radians(moon_altitude)))
                    viewing.append((math.sin(math.radians(local_radiant.altitude)) * (1 - .5 * interference), moment, local_radiant, interference))
                best = max(viewing, key=lambda sample: sample[0]) if viewing else None
                events.append(self._event(
                    "meteor_shower", title, at, duration=timedelta(days=1),
                    altitude_at_peak=round(radiant.altitude, 1), azimuth_at_peak=round(radiant.azimuth, 1),
                    radiant={"ra_degrees": ra, "declination": dec},
                    visibility_from_location="radiant_rises" if self.observer.latitude * dec >= 0 or abs(self.observer.latitude) + abs(dec) < 90 else "radiant_below_horizon",
                    moon_interference=round(moon * 100), expected_rate=rate,
                    best_viewing=({
                        "time": best[1].isoformat(), "altitude": round(best[2].altitude, 1),
                        "azimuth": round(best[2].azimuth, 1), "moon_interference": round(best[3] * 100),
                        "time_resolution_seconds": 3600,
                    } if best else None),
                    rate_definition="Ideal zenithal hourly rate, not local meteor count",
                    peak_estimate=True, calculation_method="IMO nominal solar longitude / Astronomy Engine",
                ))
        for body in (astronomy.Body.Mars, astronomy.Body.Jupiter, astronomy.Body.Saturn, astronomy.Body.Uranus, astronomy.Body.Neptune):
            cursor = _time(begin)
            for _ in range(3):
                peak = astronomy.SearchRelativeLongitude(body, 0, cursor)
                if _utc(peak) > self._horizon:
                    break
                events.append(self._event("opposition", f"{body.name} opposition", _utc(peak), body))
                cursor = peak.AddDays(1)
        for body in (astronomy.Body.Mercury, astronomy.Body.Venus):
            cursor = _time(begin)
            for _ in range(12):
                result = astronomy.SearchMaxElongation(body, cursor)
                if result is None or _utc(result.time) > self._horizon:
                    break
                side = "eastern" if result.visibility == astronomy.Visibility.Evening else "western"
                events.append(self._event(
                    "elongation", f"{body.name} greatest {side} elongation",
                    _utc(result.time), body, elongation_degrees=round(result.elongation, 1),
                    best_side="evening" if side == "eastern" else "morning",
                ))
                cursor = result.time.AddDays(1)
        cursor = _time(begin)
        for _ in range(20):
            full = astronomy.SearchMoonPhase(180, cursor, 35)
            if full is None or _utc(full) > self._horizon:
                break
            distance = astronomy.GeoMoon(full).Length() * AU_KM
            if distance <= 360000:
                events.append(self._event(
                    "close_full_moon", "Close full Moon", _utc(full), astronomy.Body.Moon,
                    distance_km=round(distance), definition="Full Moon at geocentric distance <= 360,000 km",
                ))
            cursor = full.AddDays(1)
        return sorted(
            (event for event in events if datetime.fromisoformat(event["end"]) > now and datetime.fromisoformat(event["peak"]) <= self._horizon),
            key=lambda item: item["peak"],
        )[:MAX_EVENTS]

    def get_events(self, eclipses: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
        now = utc_now(now)
        if self._events is None or self._expires is None or now >= self._expires:
            self._events = self._calculate(now)
            self._expires = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            for event in self._events:
                self._expires = min(self._expires, datetime.fromisoformat(event["end"]))
        events = list(self._events)
        # Only references and shared timings: never search eclipses a second time.
        for kind in ("solar", "lunar"):
            for eclipse in eclipses.get(kind, []):
                events.append({
                    "event_type": f"{kind}_eclipse",
                    "title": f"{eclipse['kind'].capitalize()} {kind} eclipse",
                    "start": eclipse["visible_begin"], "peak": eclipse["peak"], "end": eclipse["visible_end"],
                    "visibility_from_location": "above_horizon" if eclipse["peak_visible"] else "partial_window_only",
                    "entity_id": f"sensor.nasa_astronomy_ephemeris_eclipses_{kind}",
                    "calculation_method": "Existing EclipseProvider",
                    "significance": "eclipse",
                })
        events = sorted(events, key=lambda item: item["peak"])[:MAX_EVENTS]
        active = next((e for e in events if e["start"] <= now.isoformat() < e["end"]), None)
        return {
            "events": events, "next_event": events[0]["title"] if events else None,
            "active_event": active["title"] if active else None,
            "next_meteor_shower": next((e["title"] for e in events if e["event_type"] == "meteor_shower"), None),
            "search_end": self._horizon.isoformat(), "horizon_months": HORIZON_MONTHS,
            "calculated_at": now.isoformat(), "time_zone": "UTC",
        }
