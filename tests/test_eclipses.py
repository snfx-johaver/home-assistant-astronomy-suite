"""Eclipse prediction, local visibility, caching and entity regressions."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import astronomy

from harness import load_component_module

p = load_component_module("eclipses", subpackage="providers")
s = load_component_module("sensor_ephemeris")
UTC = timezone.utc


class EclipseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.now = datetime(2026, 11, 26, tzinfo=UTC)
        cls.amsterdam = p.EclipseProvider(52.37, 4.9, 0).get_eclipses(cls.now)
        cls.dallas = p.EclipseProvider(32.7767, -96.797, 130).get_eclipses(
            datetime(2024, 4, 8, 18, tzinfo=UTC)
        )

    def test_known_total_solar_and_lunar_eclipses(self):
        solar = self.dallas["solar"][0]
        self.assertEqual(solar["kind"], "total")
        self.assertEqual(solar["obscuration_pct"], 100)
        peak = datetime.fromisoformat(solar["peak"])
        # Published Dallas circumstances: April 8, 2024, about 18:42 UTC.
        self.assertLess(abs((peak - datetime(2024, 4, 8, 18, 42, tzinfo=UTC)).total_seconds()), 60)
        self.assertTrue(solar["peak_visible"])
        self.assertEqual(solar["begin"], solar["visible_begin"])
        self.assertEqual(solar["end"], solar["visible_end"])
        central_duration = (
            datetime.fromisoformat(solar["central_end"])
            - datetime.fromisoformat(solar["central_begin"])
        ).total_seconds()
        self.assertGreater(central_duration, 230)
        self.assertLess(central_duration, 240)
        lunar = next(e for e in self.dallas["lunar"] if e["kind"] == "total")
        self.assertLess(abs((
            datetime.fromisoformat(lunar["peak"])
            - datetime(2025, 3, 14, 6, 59, tzinfo=UTC)
        ).total_seconds()), 60)

    def test_lunar_visibility_is_local_and_does_not_require_visible_peak(self):
        self.assertNotIn("2027-08-17", [e["peak"][:10] for e in self.amsterdam["lunar"]])
        dallas = p.EclipseProvider(32.78, -96.8, 0).get_eclipses(self.now)
        self.assertIn("2027-08-17", [e["peak"][:10] for e in dallas["lunar"]])
        at_moonrise = dallas["lunar"][0]
        self.assertEqual(at_moonrise["peak"][:10], "2027-02-20")
        self.assertFalse(at_moonrise["peak_visible"])
        self.assertGreater(at_moonrise["visible_begin"], at_moonrise["peak"])
        self.assertLess(at_moonrise["visible_begin"], at_moonrise["visible_end"])

    def test_solar_sunset_clips_visibility_without_hiding_event(self):
        sunset = self.amsterdam["solar"][1]
        self.assertEqual(sunset["peak"][:10], "2028-01-26")
        self.assertFalse(sunset["peak_visible"])
        self.assertLess(sunset["visible_end"], sunset["end"])
        self.assertLess(sunset["visible_end"], sunset["peak"])

    def test_search_range_limits_and_utc_metadata(self):
        horizon = datetime.fromisoformat(self.amsterdam["search_end"])
        self.assertEqual(horizon, datetime(2028, 5, 26, tzinfo=UTC))
        for kind in ("solar", "lunar"):
            events = self.amsterdam[kind]
            self.assertLessEqual(len(events), 3)
            self.assertEqual(events, sorted(events, key=lambda e: e["peak"]))
            for event in events:
                self.assertLessEqual(datetime.fromisoformat(event["peak"]), horizon)
                self.assertGreater(datetime.fromisoformat(event["visible_end"]), self.now)
                self.assertLessEqual(event["begin"], event["visible_begin"])
                self.assertLessEqual(event["visible_end"], event["end"])
        self.assertEqual(self.amsterdam["time_zone"], "UTC")
        self.assertEqual(self.amsterdam["latitude"], 52.37)

    def test_cache_reused_until_utc_midnight_or_visible_event_end(self):
        provider = p.EclipseProvider(52.37, 4.9, 0)
        original = provider.get_eclipses(self.now)
        with patch.object(p.astronomy, "SearchLunarEclipse", wraps=astronomy.SearchLunarEclipse) as search:
            self.assertIs(provider.get_eclipses(self.now + timedelta(hours=1)), original)
            search.assert_not_called()
            provider.get_eclipses(self.now + timedelta(days=1))
            search.assert_called_once()

        provider = p.EclipseProvider(32.7767, -96.797, 130)
        during = datetime(2024, 4, 8, 19, tzinfo=UTC)
        ongoing = provider.get_eclipses(during)
        self.assertEqual(ongoing["solar"][0]["peak"][:10], "2024-04-08")
        after = datetime.fromisoformat(ongoing["solar"][0]["visible_end"]) + timedelta(seconds=1)
        finished = provider.get_eclipses(after)
        self.assertNotIn("2024-04-08", [e["peak"][:10] for e in finished["solar"]])

    def test_month_end_and_offset_input_use_real_calendar_months(self):
        provider = p.EclipseProvider(52.37, 4.9, 0)
        result = provider.get_eclipses(datetime(2026, 8, 31, 23, tzinfo=UTC))
        self.assertEqual(result["search_end"], "2028-02-29T23:00:00+00:00")
        result = p.EclipseProvider(52.37, 4.9, 0).get_eclipses(
            datetime(2026, 11, 27, 1, tzinfo=timezone(timedelta(hours=2)))
        )
        self.assertEqual(result["search_start"], "2026-11-26T23:00:00+00:00")

    def test_entity_exposes_events_and_keeps_zero_count_available(self):
        coordinator = SimpleNamespace(data={"eclipses": self.amsterdam})
        sensor = s.EphemerisSensor(
            coordinator, "eclipses", "solar", "Upcoming Solar", None,
            "mdi:weather-sunny", None, "entry",
        )
        self.assertEqual(sensor.native_value, len(self.amsterdam["solar"]))
        self.assertEqual(sensor.extra_state_attributes["events"], self.amsterdam["solar"])
        self.assertEqual(sensor.extra_state_attributes["provider"], "astronomy-engine")
        self.assertNotIn("lunar", sensor.extra_state_attributes)
        coordinator.data = {"eclipses": {**self.amsterdam, "solar": []}}
        self.assertEqual(sensor.native_value, 0)
        self.assertTrue(sensor.available)
        coordinator.data = {}
        self.assertFalse(sensor.available)
        self.assertIsNone(sensor.native_value)

    def test_coordinator_preserves_body_data_and_reports_calculation_errors(self):
        body_provider = SimpleNamespace(
            enabled_bodies=["moon"], get_ephemeris=Mock(return_value={"altitude": 12}),
            get_sky_conditions=Mock(return_value={"twilight_phase": "night"}),
        )
        eclipse_provider = Mock()
        eclipse_provider.get_eclipses.return_value = self.amsterdam
        coordinator = s.EphemerisCoordinator(None, body_provider, eclipse_provider)
        data = coordinator._fetch_all()
        self.assertEqual(data["moon"]["altitude"], 12)
        self.assertEqual(data["eclipses"], self.amsterdam)
        eclipse_provider.get_eclipses.side_effect = astronomy.Error("search failed")
        with self.assertRaisesRegex(s.UpdateFailed, "Eclipse calculation failed: search failed"):
            coordinator._fetch_all()


if __name__ == "__main__":
    unittest.main()
