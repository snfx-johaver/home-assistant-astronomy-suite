"""UTC feed boundaries and date metadata for the NEO dashboard."""

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from harness import load_component_module

coordinator_module = load_component_module("coordinator")
sensor_module = load_component_module("sensor")
const = load_component_module("const")


class Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        instant = datetime(2026, 11, 19, 0, 5, tzinfo=timezone.utc)
        if tz is not None:
            return instant.astimezone(tz)
        # A host in UTC-8 still has the previous local date.
        return datetime(2026, 11, 18, 16, 5)


class NeoProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_feed_uses_exact_utc_day_and_passes_range_to_every_neo_sensor(self):
        coordinator = object.__new__(coordinator_module.NasaDataCoordinator)
        payload = {"element_count": 0, "near_earth_objects": {"2026-11-19": []}}
        coordinator._fetch_json = AsyncMock(return_value=payload)
        with patch.object(coordinator_module, "datetime", Clock):
            result = await coordinator._fetch_neo()
        coordinator._fetch_json.assert_awaited_once_with(
            const.NEOWS_URL,
            {"start_date": "2026-11-19", "end_date": "2026-11-19"},
        )
        self.assertNotIn("start_date", payload)
        for description in sensor_module.SENSOR_DESCRIPTIONS:
            if not description.key.startswith("neo_"):
                continue
            with self.subTest(sensor=description.key):
                sensor = sensor_module.NasaAstronomySensor(
                    SimpleNamespace(data={"neo": result}),
                    description,
                    SimpleNamespace(entry_id="entry"),
                )
                attrs = sensor.extra_state_attributes
                self.assertEqual(attrs["start_date"], "2026-11-19")
                self.assertEqual(attrs["end_date"], "2026-11-19")
                self.assertEqual(attrs["date_timezone"], "UTC")
                self.assertEqual(attrs["neo_list"], [])

    async def test_failed_feed_does_not_invent_date_metadata(self):
        coordinator = object.__new__(coordinator_module.NasaDataCoordinator)
        coordinator._fetch_json = AsyncMock(return_value=None)
        self.assertIsNone(await coordinator._fetch_neo())

    def test_sensor_preserves_approach_epoch_and_nasa_hazard_flag(self):
        sensor = sensor_module.NasaAstronomySensor(
            SimpleNamespace(data={"neo": {
                "near_earth_objects": {"2026-11-19": [{
                    "id": "test",
                    "name": "Test asteroid",
                    "is_potentially_hazardous_asteroid": True,
                    "close_approach_data": [{
                        "epoch_date_close_approach": 1795053600000,
                        "close_approach_date_full": "2026-Nov-19 02:00",
                        "relative_velocity": {"kilometers_per_hour": "20000"},
                        "miss_distance": {"kilometers": "1200000"},
                    }],
                }]},
            }}),
            next(d for d in sensor_module.SENSOR_DESCRIPTIONS if d.key == "neo_count"),
            SimpleNamespace(entry_id="entry"),
        )
        attrs = sensor.extra_state_attributes
        self.assertEqual(attrs["neo_list"][0]["close_approach_timestamp"], 1795053600000)
        self.assertTrue(attrs["neo_list"][0]["hazardous"])
        self.assertEqual(attrs["hazardous_count"], 1)
