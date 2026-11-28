"""Focused local geometry, forecast fallback and bounded-entity regressions."""
import asyncio
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import astronomy

from harness import load_component_module
from test_iss_provider import sample_omm

sky = load_component_module("sky_intelligence", subpackage="providers")
forecast = load_component_module("forecast", subpackage="providers")
observing = load_component_module("observing")
space = load_component_module("space_forecast", subpackage="providers")
satellites = load_component_module("satellites")
sensors = load_component_module("sensor_intelligence")
UTC = timezone.utc


def weather_row():
    return {
        "cloud_cover": 0, "cloud_cover_low": 0, "cloud_cover_mid": 0,
        "cloud_cover_high": 0, "relative_humidity_2m": 50,
        "precipitation_probability": 0, "temperature_2m": 10,
        "dew_point_2m": 0, "wind_speed_10m": 1, "wind_gusts_10m": 2,
        "visibility": 20000,
    }


class LocalIntelligenceTests(unittest.TestCase):
    def test_event_window_order_eclipse_reuse_and_cached_search(self):
        now = datetime(2026, 11, 27, tzinfo=UTC)
        provider = sky.CelestialEventsProvider(52.3, 4.9, 0)
        eclipse = {"solar": [{"kind": "total", "visible_begin": "2027-01-01T10:00:00+00:00",
                             "peak": "2027-01-01T11:00:00+00:00", "visible_end": "2027-01-01T12:00:00+00:00", "peak_visible": True}]}
        with patch.object(astronomy, "SearchLocalSolarEclipse", side_effect=AssertionError("Duplicate eclipse search")):
            data = provider.get_events(eclipse, now)
        self.assertEqual(len([e for e in data["events"] if e["event_type"] == "solar_eclipse"]), 1)
        self.assertEqual(data["events"], sorted(data["events"], key=lambda e: e["peak"]))
        self.assertLessEqual(len(data["events"]), 48)
        self.assertEqual(data["search_end"], "2028-05-27T00:00:00+00:00")
        self.assertTrue(any(e["event_type"] == "opposition" for e in data["events"]))
        self.assertTrue(any(e["event_type"] == "elongation" for e in data["events"]))
        for event in data["events"]:
            self.assertLessEqual(event["peak"], data["search_end"])
            self.assertGreater(event["end"], now.isoformat())
        with patch.object(provider, "_calculate", side_effect=AssertionError("Unexpected recalculation")):
            provider.get_events(eclipse, now + timedelta(hours=1))

    def test_opposition_and_elongation_match_engine_definitions(self):
        now = datetime(2026, 11, 27, tzinfo=UTC)
        data = sky.CelestialEventsProvider(0, 0, 0).get_events({}, now)
        mars = next(e for e in data["events"] if e["title"] == "Mars opposition")
        expected = astronomy.SearchRelativeLongitude(astronomy.Body.Mars, 0, sky._time(now))
        self.assertLess(abs((datetime.fromisoformat(mars["peak"]) - sky._utc(expected)).total_seconds()), 1)
        venus = next(e for e in data["events"] if e["event_type"] == "elongation" and e["title"].startswith("Venus"))
        expected = astronomy.SearchMaxElongation(astronomy.Body.Venus, sky._time(now))
        self.assertAlmostEqual(venus["elongation_degrees"], expected.elongation, delta=.1)

    def test_lunar_phase_transition_apsides_and_polar_geometry(self):
        observer = astronomy.Observer(52.3, 4.9, 0)
        full = astronomy.SearchMoonPhase(180, astronomy.Time.Make(2026, 11, 1, 0, 0, 0), 35)
        before = sky.lunar_details(observer, sky._utc(full) - timedelta(minutes=1))
        after = sky.lunar_details(observer, sky._utc(full) + timedelta(minutes=1))
        self.assertLess(before["phase_longitude"], 180)
        self.assertGreater(after["phase_longitude"], 180)
        self.assertLess(before["perigee"]["distance_km"], before["apogee"]["distance_km"])
        self.assertTrue(0 <= before["age_days"] <= 30)
        self.assertEqual(len(before["sky_path"]), 25)
        self.assertEqual(before["sky_path"][0]["altitude"], before["altitude"])
        polar = astronomy.Observer(89, 0, 0)
        day = sky.horizon_at(polar, astronomy.Body.Sun, datetime(2026, 6, 21, tzinfo=UTC))
        night = sky.horizon_at(polar, astronomy.Body.Sun, datetime(2026, 12, 21, tzinfo=UTC))
        self.assertGreater(day["altitude"], 0)
        self.assertLess(night["altitude"], -18)

    def test_meteor_nominal_peak_and_southern_radiant_visibility(self):
        now = datetime(2026, 11, 27, tzinfo=UTC)
        data = sky.CelestialEventsProvider(-80, 0, 0).get_events({}, now)
        geminids = next(e for e in data["events"] if e["title"] == "Geminids")
        self.assertEqual(geminids["peak"][:10], "2026-12-14")
        self.assertTrue(geminids["peak_estimate"])
        self.assertEqual(geminids["visibility_from_location"], "radiant_below_horizon")
        self.assertIn("Ideal", geminids["rate_definition"])

    def test_quality_is_unknown_without_data_and_safety_vetoes_apply(self):
        row = weather_row()
        good = observing.quality(row, -25, -5, .9)
        self.assertEqual(good["status"], "GO")
        self.assertGreater(good["scores"]["deep_sky"], 70)
        moon = observing.quality(row, -25, 80, 1)
        self.assertLess(moon["scores"]["deep_sky"], moon["scores"]["stargazing"])
        for change in ({"precipitation_probability": 70}, {"wind_gusts_10m": 20}, {"dew_point_2m": 10, "relative_humidity_2m": 100}):
            self.assertEqual(observing.quality({**row, **change}, -25, 0, 0)["status"], "NO-GO")
        self.assertEqual(observing.quality(row, 10, 0, 0)["status"], "NO-GO")
        self.assertEqual(observing.quality({**row, "wind_gusts_10m": 20}, -25, 80, 1)["limiting_factor"], "Strong gusts")
        self.assertIsNone(observing.quality({**row, "cloud_cover": None}, -25, 0, 0)["scores"])

    def test_windows_cross_midnight_and_dst_without_losing_hours(self):
        at = datetime(2026, 10, 24, 23, tzinfo=UTC)
        rows = [{"time": (at + timedelta(hours=index)).isoformat(), "scores": {"stargazing": 80}} for index in range(5)]
        result = observing.best_window(rows)
        self.assertEqual(datetime.fromisoformat(result["end"]) - datetime.fromisoformat(result["start"]), timedelta(hours=5))
        local = [datetime.fromisoformat(row["time"]).astimezone(ZoneInfo("Europe/Amsterdam")) for row in rows]
        self.assertEqual(local[1].hour, local[2].hour)
        self.assertNotEqual(local[1].utcoffset(), local[2].utcoffset())
        self.assertIsNone(observing.best_window([]))
        self.assertIsNone(observing.best_window([{"time": at.isoformat(), "scores": None}]))

    def test_satellite_limits_geometry_and_pass_bounds(self):
        self.assertEqual(satellites.selected_ids(["25544", 25544, 20580]), [25544, 20580])
        for ids in ([0], [12.5], list(range(1, 10)), ["nan"]):
            with self.assertRaises(ValueError):
                satellites.selected_ids(ids)
        now = datetime.now(UTC)
        fields = sample_omm(now)
        satellites.parse_elements(25544)([fields])
        result = satellites.calculate_passes(fields, astronomy.Observer(52.3, 4.9, 0), now)
        self.assertLessEqual(len(result["passes"]), 6)
        self.assertLessEqual(len(result["ground_track"]), 60)
        self.assertTrue(-90 <= result["altitude"] <= 90)
        self.assertTrue(0 <= result["azimuth"] <= 360)
        self.assertGreater(result["range_km"], 0)
        self.assertGreater(len(result["passes"]), 0)
        for item in result["passes"]:
            self.assertLessEqual(item["start"], item["peak"])
            self.assertLessEqual(item["peak"], item["end"])
            self.assertLessEqual(len(item["sky_path"]), 30)
            self.assertIsInstance(item["observer_dark"], bool)
            self.assertIsInstance(item["sunlit"], bool)
        with self.assertRaises(ValueError):
            satellites.parse_elements(25544)([sample_omm(now - timedelta(days=8))])

    def test_summary_ids_availability_and_bounded_attributes(self):
        entry = SimpleNamespace(entry_id="entry")
        coordinator = SimpleNamespace(data={"score": None, "status": "UNKNOWN", "forecast": []})
        sensor = sensors.IntelligenceSensor(coordinator, entry, "observing_score", "Observing Score")
        self.assertEqual(sensor._attr_unique_id, "entry_observing_score")
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)
        coordinator.data = {"score": 75, "forecast": [{"time": "2026-11-27T23:00:00+00:00"}]}
        self.assertTrue(sensor.available)
        self.assertEqual(sensor.native_value, 75)
        self.assertEqual(len(sensor.extra_state_attributes["forecast"]), 1)


class Response:
    def __init__(self, payload=None, status=200, error=None):
        self.payload, self.status, self.error = payload, status, error
        self.headers = {"Retry-After": "3600"}

    async def __aenter__(self):
        await asyncio.sleep(0)
        if self.error:
            raise self.error
        return self

    async def __aexit__(self, *args):
        pass

    async def json(self):
        return self.payload


class Session:
    def __init__(self, responses):
        self.responses, self.calls = responses, []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class ForecastReliabilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_satellite_elements_survive_restart_without_another_request(self):
        elements = sample_omm(datetime.now(UTC))
        elements["NORAD_CAT_ID"] = 20580
        request = forecast.ForecastRequest(Session([]), "CelesTrak", "https://example.invalid", satellites.parse_elements(20580), timedelta(hours=12), timedelta(days=7))
        stored = {"20580": {"data": elements, "last_success": datetime.now(UTC).isoformat()}}
        store = SimpleNamespace(async_load=AsyncMock(return_value=stored), async_save=AsyncMock())
        coordinator = satellites.SatelliteCoordinator.__new__(satellites.SatelliteCoordinator)
        coordinator.hass = SimpleNamespace(async_add_executor_job=AsyncMock(side_effect=lambda fn, data: fn(data)))
        coordinator.ids, coordinator.requests = [20580], {20580: request}
        coordinator._restored, coordinator._saved, coordinator._pass_cache = False, None, {}
        coordinator.storage_key = "test"
        coordinator.observer = astronomy.Observer(52.3, 4.9, 0)
        with patch.dict(sys.modules, {"homeassistant.helpers.storage": SimpleNamespace(Store=lambda *args: store)}):
            data = await coordinator._async_update_data()
        self.assertEqual(request.session.calls, [])
        self.assertEqual(data["20580"]["norad_id"], 20580)
        self.assertLessEqual(len(data["20580"]["passes"]), 6)

    def test_options_menu_sections_have_labels_and_satellite_error(self):
        path = Path(__file__).resolve().parents[1] / "custom_components" / "nasa_astronomy"
        source = json.loads((path / "strings.json").read_text(encoding="utf-8"))
        english = json.loads((path / "translations" / "en.json").read_text(encoding="utf-8"))
        self.assertEqual(source, english)
        for section in ("observing", "celestial_events", "space_weather_forecast", "satellites"):
            self.assertIn("enabled", source["options"]["step"][section]["data"])
        self.assertIn("invalid_satellites", source["options"]["error"])

    async def test_concurrent_requests_and_failures_share_one_result(self):
        session = Session([Response({"value": 4}), Response(error=TimeoutError())])
        request = forecast.ForecastRequest(session, "Test", "https://example.invalid", lambda p: {"value": forecast.number(p["value"], 0, 10)}, timedelta(hours=1), timedelta(hours=6))
        values = await asyncio.gather(request.get(), request.get(), request.get())
        self.assertEqual(len(session.calls), 1)
        self.assertEqual(values, [{"value": 4}] * 3)
        self.assertEqual(session.calls[0][1]["timeout"].total, 20)
        await request.get()
        self.assertEqual(len(session.calls), 1)
        request.next_attempt = None
        with self.assertLogs(forecast._LOGGER, level="DEBUG") as logs:
            stale = await request.get()
        self.assertEqual(stale, {"value": 4})
        self.assertEqual(request.error, "TimeoutError")
        self.assertIn("cached data", logs.output[0])
        request.last_success -= timedelta(hours=7)
        self.assertIsNone(await request.get())

    async def test_malformed_and_rate_limited_requests_do_not_replace_cache(self):
        session = Session([Response({"value": 5}), Response({"value": "secret-location"}), Response(status=429)])
        request = forecast.ForecastRequest(session, "Test", "https://example.invalid", lambda p: forecast.number(p["value"], 0, 10), timedelta(hours=1), timedelta(hours=6))
        self.assertEqual(await request.get(), 5)
        for _ in range(2):
            request.next_attempt = None
            with self.assertLogs(forecast._LOGGER, level="DEBUG") as logs:
                self.assertEqual(await request.get(), 5)
            self.assertNotIn("secret-location", str(logs.output))
        self.assertGreater(request.next_attempt - datetime.now(UTC), timedelta(minutes=59))

    def test_weather_nulls_and_malformed_arrays(self):
        at = int(datetime.now(UTC).replace(minute=0, second=0, microsecond=0).timestamp())
        hourly = {"time": [at + i * 3600 for i in range(72)]}
        hourly.update({key: [value] * 72 for key, value in weather_row().items()})
        result = forecast.parse_weather({"hourly": hourly})
        self.assertEqual(len(result), 72)
        hourly["cloud_cover"][0] = None
        self.assertIsNone(forecast.parse_weather({"hourly": hourly})[0]["cloud_cover"])
        hourly["cloud_cover"].pop()
        with self.assertRaises(ValueError):
            forecast.parse_weather({"hourly": hourly})

    def test_noaa_forecast_parser_and_local_aurora_grid(self):
        rows = space.parse_kp([{"time_tag": "2026-11-27T12:00:00", "kp": 5.3, "observed": "predicted"}])
        self.assertEqual(rows[0]["kp"], 5.3)
        with self.assertRaises(ValueError):
            space.parse_kp([{"time_tag": "2026-11-27T12:00:00", "kp": 12, "observed": "predicted"}])
        payload = {"Forecast Time": "2026-11-27T12:00:00Z", "coordinates": [[359, 52, 40]] * 100}
        result = space.aurora_parser(52, -1)(payload)
        self.assertEqual(result["probability"], 40)


if __name__ == "__main__":
    unittest.main()
