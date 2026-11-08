"""Regression coverage for the cached Meteosat-12 camera."""

from __future__ import annotations

import asyncio
import logging
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from harness import load_component_module

camera = load_component_module("camera")
const = load_component_module("const")

PNG = b"\x89PNG\r\n\x1a\nmeteosat"


class FakeResponse:
    def __init__(
        self,
        body=PNG,
        *,
        status=200,
        content_type="image/png",
        enter_delay=0,
        enter_error=None,
        read_error=None,
    ):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.enter_delay = enter_delay
        self.enter_error = enter_error
        self.read_error = read_error

    async def __aenter__(self):
        if self.enter_error is not None:
            raise self.enter_error
        if self.enter_delay:
            await asyncio.sleep(self.enter_delay)
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def read(self):
        if self.read_error is not None:
            raise self.read_error
        await asyncio.sleep(0)
        return self.body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, *, timeout):
        self.calls.append((url, timeout.total))
        return self.responses.pop(0)


def make_camera():
    entity = camera.Meteosat12EarthCamera(
        SimpleNamespace(data={}),
        SimpleNamespace(entry_id="entry"),
    )
    entity.hass = SimpleNamespace(
        async_create_task=lambda coro, name: asyncio.create_task(coro, name=name)
    )
    return entity


class MeteosatCameraTests(unittest.IsolatedAsyncioTestCase):
    async def test_platform_registers_meteosat_camera(self):
        coordinator = SimpleNamespace(data={})
        hass = SimpleNamespace(
            data={
                const.DOMAIN: {
                    "entry": {"coordinator": coordinator},
                }
            }
        )
        entry = SimpleNamespace(entry_id="entry")
        registered = []

        await camera.async_setup_entry(
            hass,
            entry,
            lambda entities, update_before_add: registered.extend(entities),
        )

        meteosat = [
            entity
            for entity in registered
            if isinstance(entity, camera.Meteosat12EarthCamera)
        ]
        self.assertEqual(len(meteosat), 1)
        self.assertEqual(len(registered), 8)

    def test_registration_and_metadata(self):
        entity = make_camera()
        self.assertEqual(entity._attr_name, "Meteosat-12 Earth")
        object_id = re.sub(
            r"_+",
            "_",
            re.sub(r"[^a-z0-9]+", "_", entity._attr_name.lower()),
        ).strip("_")
        self.assertEqual(
            f"camera.astronomy_space_suite_{object_id}",
            "camera.astronomy_space_suite_meteosat_12_earth",
        )
        self.assertEqual(entity._attr_unique_id, "entry_meteosat_12_earth_camera")
        self.assertEqual(
            entity.extra_state_attributes,
            {
                "source": "EUMETSAT",
                "band": "GeoColour RGB",
                "region": "Europe/Africa",
                "update_frequency": "Every 10 minutes",
                "attribution": "EUMETSAT / NASA",
                "background": "NASA Black Marble",
            },
        )
        self.assertIsNone(getattr(entity, "entity_picture", None))

    def test_wms_url_projection_and_render_parameters(self):
        parsed = urlparse(const.METEOSAT12_EARTH_URL)
        query = parse_qs(parsed.query, keep_blank_values=True)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "view.eumetsat.int")
        self.assertEqual(parsed.path, "/geoserver/wms")
        self.assertEqual(query["service"], ["WMS"])
        self.assertEqual(query["version"], ["1.3.0"])
        self.assertEqual(query["request"], ["GetMap"])
        self.assertEqual(query["layers"], ["mtg_fd:rgb_geocolour"])
        self.assertEqual(query["bbox"], ["-6500000,-6500000,6500000,6500000"])
        self.assertEqual(query["width"], ["1200"])
        self.assertEqual(query["height"], ["1200"])
        self.assertEqual(query["srs"], ["AUTO:97004,9001,0,0"])
        self.assertEqual(query["styles"], [""])
        self.assertEqual(query["format"], ["image/png"])
        self.assertEqual(query["bgcolor"], ["0x000000"])

    async def test_success_is_cached_and_failure_keeps_last_known_png(self):
        entity = make_camera()
        session = FakeSession(
            [
                FakeResponse(PNG),
                FakeResponse(b"upstream error", status=503, content_type="text/plain"),
            ]
        )
        with patch.object(camera, "async_get_clientsession", return_value=session):
            self.assertEqual(await entity._async_refresh(), PNG)
            self.assertEqual(await entity._async_refresh(), PNG)
            self.assertEqual(await entity.async_camera_image(), PNG)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual({timeout for _, timeout in session.calls}, {25})

    async def test_malformed_and_non_image_responses_are_rejected(self):
        for response in (
            FakeResponse(b"<html>not an image</html>", content_type="text/html"),
            FakeResponse(b"not-png", content_type="image/png"),
            FakeResponse(PNG, content_type="image/jpeg"),
        ):
            with self.subTest(response.headers["Content-Type"]):
                entity = make_camera()
                session = FakeSession([response])
                with patch.object(camera, "async_get_clientsession", return_value=session):
                    self.assertIsNone(await entity._async_refresh())
                self.assertIsNone(entity._cached_image)

    async def test_cached_failures_log_only_debug_and_scheduled_refresh_recovers(self):
        for response, reason in (
            (FakeResponse(status=503), "HTTP status 503"),
            (FakeResponse(status=504), "HTTP status 504"),
            (FakeResponse(enter_error=TimeoutError()), "TimeoutError"),
            (
                FakeResponse(enter_error=camera.aiohttp.ClientError("unreachable")),
                "unreachable",
            ),
            (
                FakeResponse(read_error=camera.aiohttp.ClientError("read failed")),
                "read failed",
            ),
            (FakeResponse(b"invalid", content_type="text/html"), "invalid PNG"),
        ):
            with self.subTest(reason=reason):
                entity = make_camera()
                recovered_png = PNG + b"-new"
                session = FakeSession(
                    [FakeResponse(PNG), response, response, FakeResponse(recovered_png)]
                )
                with patch.object(camera, "async_get_clientsession", return_value=session):
                    self.assertEqual(await entity.async_camera_image(), PNG)
                    with self.assertLogs(camera._LOGGER, level=logging.DEBUG) as logs:
                        await entity._async_scheduled_refresh(None)
                        self.assertEqual(await entity.async_camera_image(), PNG)
                        await entity._async_scheduled_refresh(None)
                        self.assertEqual(await entity.async_camera_image(), PNG)
                    self.assertEqual(len(logs.records), 2)
                    for record in logs.records:
                        self.assertEqual(record.levelno, logging.DEBUG)
                        self.assertIn(reason, record.getMessage())
                    await entity._async_scheduled_refresh(None)
                    self.assertEqual(await entity.async_camera_image(), recovered_png)
                self.assertEqual(entity._cached_image, recovered_png)
                self.assertEqual(len(session.calls), 4)

    async def test_failures_without_cached_image_still_warn(self):
        for response, reason in (
            (FakeResponse(status=504), "HTTP status 504"),
            (FakeResponse(enter_error=TimeoutError()), "TimeoutError"),
            (
                FakeResponse(enter_error=camera.aiohttp.ClientError("unreachable")),
                "unreachable",
            ),
            (FakeResponse(b"invalid", content_type="text/html"), "invalid PNG"),
        ):
            with self.subTest(reason=reason):
                entity = make_camera()
                session = FakeSession([response])
                with patch.object(camera, "async_get_clientsession", return_value=session):
                    with self.assertLogs(camera._LOGGER, level=logging.WARNING) as logs:
                        self.assertIsNone(await entity.async_camera_image())
                self.assertEqual(len(logs.records), 1)
                self.assertEqual(logs.records[0].levelno, logging.WARNING)
                self.assertIn(reason, logs.records[0].getMessage())
                self.assertIsNone(entity._cached_image)

    async def test_concurrent_first_requests_share_one_download(self):
        entity = make_camera()
        session = FakeSession([FakeResponse(PNG)])
        with patch.object(camera, "async_get_clientsession", return_value=session):
            first, second = await asyncio.gather(
                entity.async_camera_image(),
                entity.async_camera_image(),
            )
        self.assertEqual(first, PNG)
        self.assertEqual(second, PNG)
        self.assertEqual(len(session.calls), 1)

    async def test_concurrent_failed_first_requests_share_one_result(self):
        entity = make_camera()
        session = FakeSession(
            [
                FakeResponse(
                    b"temporarily unavailable",
                    status=503,
                    content_type="text/plain",
                    enter_delay=0.01,
                )
            ]
        )
        with patch.object(camera, "async_get_clientsession", return_value=session):
            results = await asyncio.gather(
                entity.async_camera_image(),
                entity.async_camera_image(),
                entity.async_camera_image(),
            )
        self.assertEqual(results, [None, None, None])
        self.assertEqual(len(session.calls), 1)


if __name__ == "__main__":
    unittest.main()
