"""Regression coverage for the dynamically resolved Himawari camera."""

from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from harness import load_component_module

camera = load_component_module("camera")
const = load_component_module("const")

PNG = b"\x89PNG\r\n\x1a\nhimawari"
LATEST = {"date": "2026-10-18 18:50:00", "file": "ignored-by-url-builder.png"}
IMAGE_URL = (
    "https://himawari8.nict.go.jp/img/D531106/1d/550/"
    "2026/10/18/185000_0_0.png"
)


class FakeResponse:
    def __init__(
        self,
        body=PNG,
        *,
        status=200,
        content_type="image/png",
        enter_delay=0,
    ):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": content_type}
        self.enter_delay = enter_delay

    async def __aenter__(self):
        if self.enter_delay:
            await asyncio.sleep(self.enter_delay)
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def json(self):
        return self.body

    async def read(self):
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
    entity = camera.Himawari8EarthCamera(
        SimpleNamespace(data={}),
        SimpleNamespace(entry_id="entry"),
    )
    entity.hass = SimpleNamespace(
        async_create_task=lambda coro, name: asyncio.create_task(coro, name=name)
    )
    entity.async_write_ha_state = lambda: None
    return entity


class HimawariCameraTests(unittest.IsolatedAsyncioTestCase):
    async def test_platform_registers_dynamic_himawari_camera(self):
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

        cameras = [
            entity
            for entity in registered
            if isinstance(entity, camera.Himawari8EarthCamera)
        ]
        self.assertEqual(len(cameras), 1)
        self.assertEqual(len(registered), 8)

    async def test_latest_timestamp_builds_image_url_and_caches_png(self):
        entity = make_camera()
        session = FakeSession([FakeResponse(LATEST), FakeResponse(PNG)])

        with patch.object(camera, "async_get_clientsession", return_value=session):
            self.assertEqual(await entity.async_camera_image(), PNG)
            self.assertEqual(await entity.async_camera_image(), PNG)

        self.assertEqual(
            session.calls,
            [
                (const.HIMAWARI8_LATEST_URL, 25),
                (IMAGE_URL, 25),
            ],
        )
        self.assertEqual(entity.entity_picture, IMAGE_URL)
        self.assertEqual(entity.extra_state_attributes["image_url"], IMAGE_URL)

    async def test_failed_refresh_keeps_last_good_image_and_url(self):
        entity = make_camera()
        session = FakeSession(
            [
                FakeResponse(LATEST),
                FakeResponse(PNG),
                FakeResponse({"date": "2026-10-18 19:00:00"}),
                FakeResponse(b"upstream error", status=503, content_type="text/plain"),
            ]
        )

        with patch.object(camera, "async_get_clientsession", return_value=session):
            await entity._async_refresh()
            self.assertEqual(await entity._async_refresh(), PNG)

        self.assertEqual(entity.entity_picture, IMAGE_URL)
        self.assertEqual(len(session.calls), 4)

    async def test_invalid_timestamp_does_not_request_an_image(self):
        entity = make_camera()
        session = FakeSession([FakeResponse({"date": "not a timestamp"})])

        with patch.object(camera, "async_get_clientsession", return_value=session):
            self.assertIsNone(await entity.async_camera_image())

        self.assertEqual(session.calls, [(const.HIMAWARI8_LATEST_URL, 25)])
        self.assertIsNone(entity.entity_picture)

    async def test_non_png_image_is_rejected(self):
        entity = make_camera()
        session = FakeSession(
            [
                FakeResponse(LATEST),
                FakeResponse(b"not a png", content_type="text/plain"),
            ]
        )

        with patch.object(camera, "async_get_clientsession", return_value=session):
            self.assertIsNone(await entity.async_camera_image())

        self.assertIsNone(entity.entity_picture)

    async def test_concurrent_first_requests_share_one_refresh(self):
        entity = make_camera()
        session = FakeSession(
            [
                FakeResponse(LATEST, enter_delay=0.01),
                FakeResponse(PNG),
            ]
        )

        with patch.object(camera, "async_get_clientsession", return_value=session):
            results = await asyncio.gather(
                entity.async_camera_image(),
                entity.async_camera_image(),
                entity.async_camera_image(),
            )

        self.assertEqual(results, [PNG, PNG, PNG])
        self.assertEqual(len(session.calls), 2)


if __name__ == "__main__":
    unittest.main()
