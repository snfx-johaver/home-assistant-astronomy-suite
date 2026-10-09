"""Regression coverage for NASA's migrated APOD API."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import load_component_module  # noqa: E402

const = load_component_module("const")
coordinator_module = load_component_module("coordinator")


def make_coordinator():
    """Build a coordinator without Home Assistant runtime dependencies."""
    return object.__new__(coordinator_module.NasaDataCoordinator)


class ApodProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetches_latest_entry_from_nasa_science(self):
        coordinator = make_coordinator()
        payload = {
            "date": "2026-09-29",
            "title": "Sky Swirl",
            "media_type": "image",
            "url": "https://science.nasa.gov/image-article/sky-swirl/",
            "permalink": "https://science.nasa.gov/image-article/sky-swirl/",
            "hdurl": "https://assets.science.nasa.gov/sky-swirl.jpg",
            "explanation": "<strong>Explanation:</strong> A spiral sky.",
        }
        coordinator._fetch_json_noauth = AsyncMock(return_value=[payload])

        result = await coordinator._fetch_apod()

        coordinator._fetch_json_noauth.assert_awaited_once_with(
            const.APOD_URL,
            {"per_page": "1"},
        )
        self.assertEqual(result["url"], payload["hdurl"])
        self.assertEqual(result["page_url"], payload["permalink"])
        self.assertEqual(result["explanation"], "A spiral sky.")

    async def test_migration_notice_uses_the_original_rollover_image(self):
        coordinator = make_coordinator()
        payload = {
            "date": "2026-09-28",
            "title": "Cosmic Latte",
            "media_type": "image",
            "permalink": "https://science.nasa.gov/image-article/cosmic-latte/",
            "hdurl": "https://assets.science.nasa.gov/CosmicLatte_annotated.jpg",
            "alt": (
                "A latte color image noting that apod.nasa.gov is moving "
                "to science.nasa.gov/apod."
            ),
            "basic_html": (
                '<a onMouseOver="document.imagename1.src='
                "'https://assets.science.nasa.gov/cosmiclatte_original.jpg';"
                '"><img src="https://assets.science.nasa.gov/'
                'CosmicLatte_annotated.jpg"></a>'
            ),
        }
        coordinator._fetch_json_noauth = AsyncMock(return_value=[payload])

        result = await coordinator._fetch_apod()

        self.assertEqual(
            result["url"],
            "https://assets.science.nasa.gov/cosmiclatte_original.jpg",
        )
        self.assertNotIn("apod.nasa.gov", result["url"])

    def test_video_source_is_extracted_from_basic_html(self):
        result = coordinator_module.NasaDataCoordinator._normalize_apod(
            {
                "date": "2026-09-09",
                "title": "Witness XZ Andromedae Wink",
                "media_type": "video",
                "permalink": "https://science.nasa.gov/image-article/xz-and/",
                "hdurl": "https://assets.science.nasa.gov/xz-and-poster.jpg",
                "basic_html": (
                    '<video controls><source src="https://assets.science.nasa.gov/'
                    'xz-and.mp4" type="video/mp4"></video>'
                ),
            }
        )

        self.assertEqual(result["media_type"], "video")
        self.assertEqual(
            result["url"],
            "https://assets.science.nasa.gov/xz-and.mp4",
        )
        self.assertEqual(
            result["hdurl"],
            "https://assets.science.nasa.gov/xz-and-poster.jpg",
        )

    def test_empty_or_malformed_payload_is_rejected(self):
        self.assertIsNone(
            coordinator_module.NasaDataCoordinator._normalize_apod([])
        )
        self.assertIsNone(
            coordinator_module.NasaDataCoordinator._normalize_apod({"title": "No media"})
        )


if __name__ == "__main__":
    unittest.main()
