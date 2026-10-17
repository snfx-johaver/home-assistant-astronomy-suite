"""All nine bodies must remain fresh across supported refresh intervals."""
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from harness import load_component_module

provider_module = load_component_module('openastronomy_ephemeris', subpackage='providers')

class Clock(datetime):
    current = datetime(2026, 10, 17, 3, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.current if tz is None else cls.current.astimezone(tz)

class AllBodiesRefreshTests(unittest.TestCase):
    def test_all_bodies_are_fresh_through_two_hours_at_fastest_interval(self):
        Clock.current = datetime(2026, 10, 17, 3, 0, tzinfo=timezone.utc)
        with patch.object(provider_module, 'datetime', Clock):
            provider = provider_module.OpenAstronomyEphemerisProvider(
                latitude=40, longitude=-105, update_interval=300,
                enabled_bodies={body: True for body in provider_module.BODY_LIST},
            )
            previous = {}
            for cycle in range(25):
                current = {body: provider.get_ephemeris(body) for body in provider.enabled_bodies}
                for body, result in current.items():
                    self.assertIsNotNone(result, f'{body} unavailable on cycle {cycle}')
                    self.assertIsNot(result, previous.get(body), f'{body} stale on cycle {cycle}')
                previous = current
                Clock.current += timedelta(seconds=300)

if __name__ == '__main__':
    unittest.main()
