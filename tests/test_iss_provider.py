"""Regression tests for the resilient ISS position provider chain."""

from __future__ import annotations

import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, Mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import load_component_module  # noqa: E402

const = load_component_module("const")
coordinator_module = load_component_module("coordinator")


def make_coordinator():
    """Build a coordinator without depending on Home Assistant's base class."""
    coordinator = object.__new__(coordinator_module.NasaDataCoordinator)
    coordinator._iss_omm = None
    coordinator._iss_omm_epoch = None
    coordinator._iss_omm_refresh_attempted_at = None
    coordinator._iss_omm_last_attempt_succeeded = False
    coordinator.data = {}
    return coordinator


def sample_omm(epoch: datetime | None = None) -> dict[str, str]:
    """Return valid ISS-like OMM fields for local propagation tests."""
    epoch_text = (epoch or datetime(2026, 9, 15, 12, tzinfo=timezone.utc)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )
    return {
        "CLASSIFICATION_TYPE": "U",
        "OBJECT_ID": "1998-067A",
        "EPHEMERIS_TYPE": "0",
        "ELEMENT_SET_NO": "999",
        "REV_AT_EPOCH": "49000",
        "EPOCH": epoch_text,
        "ARG_OF_PERICENTER": "78.0",
        "BSTAR": "0.00015",
        "ECCENTRICITY": "0.0007",
        "INCLINATION": "51.64",
        "MEAN_ANOMALY": "20.0",
        "MEAN_MOTION_DDOT": "0.0",
        "MEAN_MOTION_DOT": "0.0001",
        "MEAN_MOTION": "15.5",
        "RA_OF_ASC_NODE": "120.0",
        "NORAD_CAT_ID": "25544",
    }


class IssProviderValidationTests(unittest.TestCase):
    """Provider payloads must be current, finite, and geographically valid."""

    def test_wtia_payload_maps_to_existing_sensor_shape(self):
        now = 1_789_472_376
        result = coordinator_module.NasaDataCoordinator._normalize_iss_position(
            {
                "latitude": -46.533,
                "longitude": -12.330,
                "timestamp": now,
                "velocity": 27580.0,
            },
            "Where The ISS At",
            now=now,
        )

        self.assertEqual(
            result,
            {
                "iss_position": {
                    "latitude": -46.533,
                    "longitude": -12.330,
                },
                "timestamp": now,
                "source": "Where The ISS At",
                "stale": False,
            },
        )

    def test_invalid_or_stale_payloads_are_rejected(self):
        now = 1_789_472_376
        invalid = (
            None,
            {},
            {"latitude": 91, "longitude": 0, "timestamp": now},
            {"latitude": 0, "longitude": 181, "timestamp": now},
            {"latitude": "nan", "longitude": 0, "timestamp": now},
            {"latitude": 0, "longitude": 0, "timestamp": now - 121},
            {"latitude": 0, "longitude": 0, "timestamp": now + 31},
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertIsNone(
                    coordinator_module.NasaDataCoordinator._normalize_iss_position(
                        payload,
                        "provider",
                        now=now,
                    )
                )


class IssProviderChainTests(unittest.IsolatedAsyncioTestCase):
    """The chain prefers HTTPS, then local propagation, then legacy HTTP."""

    async def test_primary_wtia_response_wins(self):
        coordinator = make_coordinator()
        now = int(time.time())
        coordinator._fetch_json_noauth = AsyncMock(
            return_value={"latitude": 10, "longitude": 20, "timestamp": now}
        )
        coordinator._refresh_iss_orbit_elements = AsyncMock()

        result = await coordinator._fetch_iss_position()

        self.assertEqual(result["source"], "Where The ISS At")
        self.assertEqual(result["iss_position"], {"latitude": 10.0, "longitude": 20.0})
        coordinator._fetch_json_noauth.assert_awaited_once_with(
            const.ISS_POSITION_URL
        )
        coordinator._refresh_iss_orbit_elements.assert_awaited_once()

    async def test_celestrak_local_propagation_is_first_fallback(self):
        coordinator = make_coordinator()
        coordinator._fetch_json_noauth = AsyncMock(return_value=None)
        coordinator._refresh_iss_orbit_elements = AsyncMock()
        propagated = {
            "iss_position": {"latitude": 1.0, "longitude": 2.0},
            "timestamp": int(time.time()),
            "source": "CelesTrak (local SGP4)",
            "stale": False,
        }
        coordinator._propagate_iss_position = Mock(return_value=propagated)

        result = await coordinator._fetch_iss_position()

        self.assertIs(result, propagated)
        coordinator._fetch_json_noauth.assert_awaited_once_with(
            const.ISS_POSITION_URL
        )

    async def test_open_notify_remains_last_legacy_fallback(self):
        coordinator = make_coordinator()
        now = int(time.time())

        async def fetch(url, params=None):
            if url == const.ISS_LEGACY_POSITION_URL:
                return {
                    "message": "success",
                    "timestamp": now,
                    "iss_position": {"latitude": "3.5", "longitude": "-4.5"},
                }
            return None

        coordinator._fetch_json_noauth = AsyncMock(side_effect=fetch)
        coordinator._refresh_iss_orbit_elements = AsyncMock()
        coordinator._propagate_iss_position = Mock(return_value=None)

        result = await coordinator._fetch_iss_position()

        self.assertEqual(result["source"], "Open Notify")
        self.assertEqual(
            result["iss_position"],
            {"latitude": 3.5, "longitude": -4.5},
        )

    async def test_last_valid_position_is_retained_as_stale(self):
        coordinator = make_coordinator()
        previous = {
            "iss_position": {"latitude": 5.0, "longitude": 6.0},
            "timestamp": int(time.time()) - 600,
            "source": "Where The ISS At",
            "stale": False,
        }
        coordinator.data = {"iss_position": previous}
        for name in (
            "_fetch_apod",
            "_fetch_neo",
            "_fetch_donki_cme",
            "_fetch_donki_flr",
            "_fetch_donki_gst",
            "_fetch_eonet",
            "_fetch_techtransfer",
            "_fetch_rocket_launches",
            "_fetch_iss_position",
            "_fetch_epic_earth",
            "_fetch_swpc_kp_index",
        ):
            setattr(coordinator, name, AsyncMock(return_value=None))

        result = await coordinator._async_update_data()

        self.assertEqual(result["iss_position"]["iss_position"], previous["iss_position"])
        self.assertEqual(result["iss_position"]["timestamp"], previous["timestamp"])
        self.assertTrue(result["iss_position"]["stale"])

    async def test_expired_last_known_position_is_not_published(self):
        coordinator = make_coordinator()
        coordinator.data = {
            "iss_position": {
                "iss_position": {"latitude": 5.0, "longitude": 6.0},
                "timestamp": int(time.time())
                - coordinator_module.ISS_LAST_KNOWN_MAX_AGE_SECONDS
                - 1,
                "source": "Where The ISS At",
                "stale": False,
            }
        }
        for name in (
            "_fetch_apod",
            "_fetch_neo",
            "_fetch_donki_cme",
            "_fetch_donki_flr",
            "_fetch_donki_gst",
            "_fetch_eonet",
            "_fetch_techtransfer",
            "_fetch_rocket_launches",
            "_fetch_iss_position",
            "_fetch_epic_earth",
            "_fetch_swpc_kp_index",
        ):
            setattr(coordinator, name, AsyncMock(return_value=None))

        result = await coordinator._async_update_data()

        self.assertIsNone(result["iss_position"])


class IssOrbitFallbackTests(unittest.IsolatedAsyncioTestCase):
    """CelesTrak data is cached politely and produces a valid ground point."""

    async def test_refresh_is_limited_to_once_per_two_hours(self):
        coordinator = make_coordinator()
        coordinator._fetch_json_noauth = AsyncMock(
            return_value=[sample_omm(datetime.now(timezone.utc))]
        )

        await coordinator._refresh_iss_orbit_elements()
        await coordinator._refresh_iss_orbit_elements()

        coordinator._fetch_json_noauth.assert_awaited_once_with(
            const.ISS_ORBIT_ELEMENTS_URL
        )
        self.assertEqual(coordinator._iss_omm["NORAD_CAT_ID"], "25544")

    async def test_failed_refresh_retries_after_shorter_backoff(self):
        coordinator = make_coordinator()
        coordinator._fetch_json_noauth = AsyncMock(
            side_effect=[
                None,
                [sample_omm(datetime.now(timezone.utc))],
            ]
        )

        await coordinator._refresh_iss_orbit_elements()
        await coordinator._refresh_iss_orbit_elements()
        self.assertEqual(coordinator._fetch_json_noauth.await_count, 1)

        coordinator._iss_omm_refresh_attempted_at -= timedelta(minutes=16)
        await coordinator._refresh_iss_orbit_elements()
        self.assertEqual(coordinator._fetch_json_noauth.await_count, 2)
        self.assertTrue(coordinator._iss_omm_last_attempt_succeeded)

    def test_cached_omm_propagates_to_finite_valid_coordinates(self):
        coordinator = make_coordinator()
        coordinator._iss_omm = sample_omm()
        coordinator._iss_omm_epoch = datetime(
            2026, 9, 15, 12, tzinfo=timezone.utc
        )

        result = coordinator._propagate_iss_position(
            datetime(2026, 9, 15, 12, 5, tzinfo=timezone.utc)
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "CelesTrak (local SGP4)")
        latitude = result["iss_position"]["latitude"]
        longitude = result["iss_position"]["longitude"]
        self.assertAlmostEqual(latitude, 44.24423, places=4)
        self.assertAlmostEqual(longitude, 74.21928, places=4)

    def test_expired_cached_omm_is_not_propagated_as_current(self):
        coordinator = make_coordinator()
        coordinator._iss_omm = sample_omm()
        coordinator._iss_omm_epoch = datetime(
            2026, 9, 1, 12, tzinfo=timezone.utc
        )

        result = coordinator._propagate_iss_position(
            datetime(2026, 9, 15, 12, tzinfo=timezone.utc)
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
