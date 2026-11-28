"""NOAA SWPC forecasts shared by the existing NASA coordinator."""
from datetime import timedelta

from .forecast import ForecastRequest, number, stamp

BASE = "https://services.swpc.noaa.gov/"


def parse_kp(payload):
    if not isinstance(payload, list) or not payload:
        raise ValueError("Missing Kp forecast")
    rows = []
    for item in payload[-80:]:
        kind = item["observed"]
        if kind not in ("observed", "estimated", "predicted"):
            raise ValueError("Unknown Kp forecast type")
        rows.append({"time": stamp(item["time_tag"]).isoformat(), "kp": number(item["kp"], 0, 9), "kind": kind})
    return sorted(rows, key=lambda row: row["time"])


def parse_probabilities(payload):
    if not isinstance(payload, list) or not payload:
        raise ValueError("Missing solar forecast")
    latest = max(payload, key=lambda item: stamp(item["date"]))
    return {
        "issued": stamp(latest["date"]).isoformat(),
        "days": [
            {"day": day, "m_class_probability": number(latest[f"m_class_{day}_day"], 0, 100),
             "x_class_probability": number(latest[f"x_class_{day}_day"], 0, 100),
             "radiation_probability": number(latest[f"10mev_protons_{day}_day"], 0, 100)}
            for day in range(1, 4)
        ],
        "polar_cap_absorption": latest.get("polar_cap_absorption"),
    }


def parse_scales(payload):
    result = []
    for key in ("0", "1", "2", "3"):
        item = payload[key]
        result.append({
            "date": stamp(f"{item['DateStamp']}T{item['TimeStamp']}").isoformat(),
            "day": int(key),
            **{scale: int(number(item[scale]["Scale"], 0, 5)) if item[scale]["Scale"] is not None else None for scale in ("R", "S", "G")},
        })
    return result


def parse_solar_cycle(payload):
    if not isinstance(payload, list) or not payload:
        raise ValueError("Missing solar cycle observations")
    result = []
    for item in payload[-12:]:
        date = item["time-tag"]
        stamp(date + "-01")
        result.append({
            "month": date, "sunspots": number(item["ssn"], 0, 1000),
            "solar_flux_sfu": number(item["f10.7"], 0, 1000),
        })
    return result


def aurora_parser(latitude, longitude):
    def parse(payload):
        coordinates = payload["coordinates"]
        if not isinstance(coordinates, list) or not 100 <= len(coordinates) <= 70000:
            raise ValueError("Incomplete aurora grid")
        nearest = None
        distance = float("inf")
        for item in coordinates:
            if not isinstance(item, list) or len(item) != 3:
                raise ValueError("Malformed aurora grid")
            lon, lat, probability = (number(item[0], 0, 360), number(item[1], -90, 90), number(item[2], 0, 100))
            delta_lon = (lon - longitude + 180) % 360 - 180
            delta = (lat - latitude) ** 2 + delta_lon ** 2
            if delta < distance:
                distance, nearest = delta, probability
        if distance > 4:
            raise ValueError("No nearby aurora cell")
        return {"time": stamp(payload["Forecast Time"]).isoformat(), "probability": nearest}
    return parse


class SpaceForecast:
    def __init__(self, session, latitude, longitude):
        self.requests = {
            "kp": ForecastRequest(session, "NOAA Kp", BASE + "products/noaa-planetary-k-index-forecast.json", parse_kp, timedelta(hours=1), timedelta(hours=6)),
            "solar": ForecastRequest(session, "NOAA solar", BASE + "json/solar_probabilities.json", parse_probabilities, timedelta(hours=3), timedelta(hours=12)),
            "scales": ForecastRequest(session, "NOAA scales", BASE + "products/noaa-scales.json", parse_scales, timedelta(hours=1), timedelta(hours=6)),
            "aurora": ForecastRequest(session, "NOAA aurora", BASE + "json/ovation_aurora_latest.json", aurora_parser(latitude, longitude), timedelta(minutes=30), timedelta(hours=2)),
            "solar_cycle": ForecastRequest(session, "NOAA solar cycle", BASE + "json/solar-cycle/observed-solar-cycle-indices.json", parse_solar_cycle, timedelta(days=1), timedelta(days=7)),
        }

    async def get(self):
        import asyncio
        from datetime import datetime, timezone

        names = list(self.requests)
        values = await asyncio.gather(*(self.requests[name].get() for name in names))
        data = dict(zip(names, values))
        now = datetime.now(timezone.utc)
        if data["kp"]:
            data["kp"] = [row for row in data["kp"] if now - timedelta(hours=24) <= stamp(row["time"]) <= now + timedelta(days=3)]
        if data["solar"] and now - stamp(data["solar"]["issued"]) > timedelta(days=2):
            data["solar"] = None
        if data["scales"]:
            data["scales"] = [
                row for row in data["scales"]
                if now - timedelta(days=1) <= stamp(row["date"]) <= now + timedelta(days=4)
            ]
        if data["aurora"] and abs((stamp(data["aurora"]["time"]) - now).total_seconds()) > 7200:
            data["aurora"] = None
        data["providers"] = {name: request.diagnostics() for name, request in self.requests.items()}
        data["stale"] = any(item["stale"] for item in data["providers"].values())
        data["available"] = bool(data["kp"] or data["solar"] or data["scales"])
        return data
