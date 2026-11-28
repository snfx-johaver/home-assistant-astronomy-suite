"""Single optional weather coordinator and local observing-quality model."""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

import astronomy
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .providers.forecast import ForecastRequest, WEATHER_FIELDS, parse_weather, stamp
from .providers.sky_intelligence import horizon_at
from .providers.eclipses import _time

_LOGGER = logging.getLogger(__name__)
WEIGHTS = {
    "stargazing": {"clouds": .45, "moonlight": .10, "seeing": .10, "transparency": .20, "wind": .15},
    "deep_sky": {"clouds": .40, "moonlight": .25, "seeing": .05, "transparency": .20, "wind": .10},
    "astrophotography": {"clouds": .40, "moonlight": .15, "seeing": .15, "transparency": .15, "wind": .15},
}


def quality(row: dict, sun_altitude: float, moon_altitude: float, illumination: float) -> dict:
    if any(row.get(key) is None for key in WEATHER_FIELDS):
        return {"scores": None, "status": "UNKNOWN", "limiting_factor": "Forecast incomplete"}
    wind = row["wind_speed_10m"]
    gusts = row["wind_gusts_10m"]
    spread = row["temperature_2m"] - row["dew_point_2m"]
    fog = max(0, min(100, (3 - spread) / 3 * 100)) if row["relative_humidity_2m"] >= 85 else 0
    moon = illumination * max(0, math.sin(math.radians(moon_altitude))) * 100
    seeing = max(0, min(100, 100 - wind * 3 - max(0, gusts - wind) * 2))
    transparency = max(0, min(100, 100 - row["cloud_cover_high"] * .5 - max(0, row["relative_humidity_2m"] - 60) - fog * .3))
    components = {
        "clouds": row["cloud_cover"], "moonlight": moon, "seeing": 100 - seeing,
        "transparency": 100 - transparency, "wind": min(100, gusts * 4),
    }
    labels = {"clouds": "Clouds", "moonlight": "Moonlight", "seeing": "Unsteady air", "transparency": "Haze or humidity", "wind": "Wind"}
    safety = sun_altitude >= -12 or row["precipitation_probability"] >= 50 or gusts >= 15 or fog >= 80
    scores = {}
    for mode, weights in WEIGHTS.items():
        score = 100 - sum(components[key] * weight for key, weight in weights.items())
        if sun_altitude > -18:
            score = min(score, 40)
        if safety:
            score = 0
        scores[mode] = int(round(max(0, min(100, score)) / 5) * 5)
    limiting = (
        "Daylight" if sun_altitude >= -12 else "Rain risk" if row["precipitation_probability"] >= 50
        else "Strong gusts" if gusts >= 15 else "Fog risk" if fog >= 80
        else "Twilight" if sun_altitude > -18 else labels[max(components, key=components.get)]
    )
    return {
        "scores": scores, "status": "GO" if scores["stargazing"] >= 70 else "MARGINAL" if scores["stargazing"] >= 40 else "NO-GO",
        "limiting_factor": limiting, "seeing_estimate": round(seeing),
        "transparency_estimate": round(transparency), "fog_risk": round(fog), "moon_interference": round(moon),
    }


def best_window(rows: list[dict], mode: str = "stargazing") -> dict | None:
    spans = []
    current = []
    for row in rows:
        if row.get("scores") and row["scores"][mode] >= 70:
            if current and stamp(row["time"]) - stamp(current[-1]["time"]) != timedelta(hours=1):
                spans.append(current)
                current = []
            current.append(row)
        elif current:
            spans.append(current)
            current = []
    if current:
        spans.append(current)
    if not spans:
        return None
    selected = max(spans, key=lambda span: (len(span), sum(r["scores"][mode] for r in span)))
    return {
        "start": selected[0]["time"], "end": (stamp(selected[-1]["time"]) + timedelta(hours=1)).isoformat(),
        "score": round(sum(row["scores"][mode] for row in selected) / len(selected)),
    }


class ObservingCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name="Astronomy observing", update_interval=timedelta(minutes=15))
        self.hass = hass
        self.entry_id = entry.entry_id
        config = entry.options.get("ephemeris", {})
        self.observer = astronomy.Observer(
            config.get("latitude", hass.config.latitude), config.get("longitude", hass.config.longitude),
            config.get("elevation", hass.config.elevation or 0),
        )
        self.request = ForecastRequest(
            async_get_clientsession(hass), "Open-Meteo", "https://api.open-meteo.com/v1/forecast",
            parse_weather, timedelta(hours=1), timedelta(hours=6),
        )

    async def _async_update_data(self):
        rows = await self.request.get({
            "latitude": self.observer.latitude, "longitude": self.observer.longitude,
            "hourly": ",".join(WEATHER_FIELDS), "forecast_days": 3,
            "timeformat": "unixtime", "timezone": "UTC", "wind_speed_unit": "ms",
        })
        if rows is None:
            return {"score": None, "status": "UNKNOWN", "forecast": [], **self.request.diagnostics()}
        deep_sky = self.hass.data.get("nasa_astronomy", {}).get(self.entry_id, {}).get("deepsky_coordinator")
        targets = dict(deep_sky.data or {}) if deep_sky else {}
        result = await self.hass.async_add_executor_job(self._calculate, rows, targets)
        return {**result, **self.request.diagnostics(), "provider": "Open-Meteo", "model": "heuristic-v1"}

    def _calculate(self, rows, targets=None):
        now = datetime.now(timezone.utc)
        forecast = []
        for row in rows:
            at = stamp(row["time"])
            if at + timedelta(hours=1) <= now or at > now + timedelta(hours=48):
                continue
            sun = horizon_at(self.observer, astronomy.Body.Sun, at)["altitude"]
            moon = horizon_at(self.observer, astronomy.Body.Moon, at)["altitude"]
            illumination = astronomy.Illumination(astronomy.Body.Moon, _time(at)).phase_fraction
            forecast.append({
                **row, "sun_altitude": sun, "moon_altitude": moon,
                "astronomical_darkness": sun < -18,
                **quality(row, sun, moon, illumination),
            })
            if len(forecast) == 48:
                break
        current = forecast[0] if forecast else {}
        window = best_window(forecast)
        planned = []
        if window and targets:
            from .sensor_deepsky import _compute_alt_az

            times = [stamp(row["time"]) for row in forecast if window["start"] <= row["time"] < window["end"]]
            for target in targets.values():
                if "ra_hours" not in target or not times:
                    continue
                samples = [(at, _compute_alt_az(target["ra_hours"], target["dec_degrees"], self.observer.latitude, self.observer.longitude, at)[0]) for at in times]
                peak, altitude = max(samples, key=lambda pair: pair[1])
                if altitude >= 20:
                    planned.append({"name": target["name"], "peak": peak.isoformat(), "altitude": round(altitude), "magnitude": target["magnitude"]})
            planned.sort(key=lambda target: target["altitude"], reverse=True)
        return {
            "score": (current.get("scores") or {}).get("stargazing"),
            "status": current.get("status", "UNKNOWN"),
            "limiting_factor": current.get("limiting_factor", "Forecast unavailable"),
            "forecast": forecast, "best_window": window, "targets": planned[:5],
            "windows": {mode: best_window(forecast, mode) for mode in WEIGHTS},
        }
