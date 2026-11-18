"""Numerical regressions for issue #81; reference values from PyEphem 4.2.1."""

import math
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from harness import load_component_module

p = load_component_module("openastronomy_ephemeris", subpackage="providers")

# Geocentric apparent RA/Dec of date, in degrees (no observer parallax).
REFERENCES = {
    (2026, 1, 1): {
        "sun": (281.724755, -23.000236),
        "moon": (67.355284, 26.929222),
        "mercury": (268.872029, -24.027056),
        "venus": (280.342622, -23.611699),
        "mars": (284.053511, -23.705944),
        "jupiter": (113.095414, 21.983889),
        "saturn": (357.391975, -3.590881),
        "uranus": (55.730790, 19.508326),
        "neptune": (0.080314, -1.417267),
    },
    (2026, 11, 16): {
        "sun": (231.469423, -18.733560),
        "moon": (312.513427, -19.119748),
        "mercury": (214.087616, -11.211987),
        "venus": (200.802083, -10.006571),
        "mars": (148.793389, 14.721269),
        "jupiter": (148.395717, 13.591042),
        "saturn": (8.825203, 0.932461),
        "uranus": (62.120449, 20.814904),
        "neptune": (2.222677, -0.570480),
    },
    (2027, 7, 1): {
        "sun": (99.981936, 23.120132),
        "moon": (55.426689, 24.758205),
        "mercury": (87.868036, 18.732459),
        "venus": (87.499469, 23.278154),
        "mars": (173.095488, 3.691326),
        "jupiter": (147.759253, 13.996458),
        "saturn": (25.525166, 7.992194),
        "uranus": (65.966603, 21.495997),
        "neptune": (6.651905, 1.343087),
    },
}


def separation(first, second):
    ra1, dec1, ra2, dec2 = map(math.radians, (*first, *second))
    cosine = (
        math.sin(dec1) * math.sin(dec2)
        + math.cos(dec1) * math.cos(dec2) * math.cos(ra1 - ra2)
    )
    return math.degrees(math.acos(max(-1, min(1, cosine))))


def coordinates(body, jd):
    if body == "sun":
        position = p._sun_position(jd)
    elif body == "moon":
        position = p._moon_position(jd)
    else:
        position = p._planet_position(body, jd)
    return p._ecliptic_to_equatorial(
        position["ecliptic_lon"], position["ecliptic_lat"], p._obliquity(jd)
    )


class EphemerisAccuracyTests(unittest.TestCase):
    def test_positions_against_independent_reference_across_seasons(self):
        for date, bodies in REFERENCES.items():
            jd = p._julian_day(datetime(*date, 5, tzinfo=timezone.utc))
            for body, expected in bodies.items():
                with self.subTest(date=date, body=body):
                    limit = 0.4 if body == "moon" else 0.3 if body == "saturn" else 0.15
                    self.assertLess(separation(coordinates(body, jd), expected), limit)

    def test_mars_jupiter_conjunction_is_not_falsely_near_coincident(self):
        jd = p._julian_day(datetime(2026, 11, 16, 5, tzinfo=timezone.utc))
        self.assertAlmostEqual(
            separation(coordinates("mars", jd), coordinates("jupiter", jd)),
            1.19379,
            delta=0.1,
        )

    def test_moon_illumination_uses_actual_sun_moon_separation(self):
        for date, expected in (
            ((2026, 1, 1), 92.7502),
            ((2026, 6, 21), 42.7803),
            ((2026, 11, 16), 37.8935),
            ((2027, 7, 1), 12.0827),
        ):
            with self.subTest(date=date):
                jd = p._julian_day(datetime(*date, 5, tzinfo=timezone.utc))
                self.assertAlmostEqual(
                    p._moon_position(jd)["illumination_pct"], expected, delta=0.4
                )

    def test_equation_of_time_uses_solar_coordinates_of_date(self):
        # PyEphem Sun RA combined with the mean solar longitude, in minutes.
        jd = p._julian_day(datetime(2026, 11, 16, 5, tzinfo=timezone.utc))
        self.assertAlmostEqual(p._equation_of_time(jd), 15.18, delta=0.5)


class VisibilityWindowTests(unittest.TestCase):
    def setUp(self):
        self.provider = p.OpenAstronomyEphemerisProvider(51.5, 0)
        self.jd = p._julian_day(datetime(2026, 11, 16, 5, tzinfo=timezone.utc))

    def test_interval_overlaps_wrap_in_either_direction(self):
        for dusk, dawn, rise, setting, expected in (
            (18, 6, 20, 4, (20, 4)),
            (18, 6, 2, 10, (2, 6)),
            (18, 6, 16, 22, (18, 22)),
            (4, 12, 2, 10, (4, 10)),
            (18, 6, 8, 16, (None, None)),
            (18, 6, 6, 18, (None, None)),
            (18, 6, 2, 22, (18, 22)),
        ):
            with self.subTest(dusk=dusk, dawn=dawn, rise=rise, setting=setting):
                with patch.object(p, "_find_rise_set_transit", side_effect=[
                    {"rise": dawn, "set": dusk},
                    {"rise": rise, "set": setting},
                ]):
                    self.assertEqual(
                        self.provider._find_visibility_window(0, 0, self.jd), expected
                    )

    def test_polar_and_circumpolar_cases(self):
        for sun_times, obj_times, altitudes, expected in (
            ({"rise": None, "set": None}, {"rise": 20, "set": 4}, [-30], (20, 4)),
            ({"rise": None, "set": None}, {"rise": 20, "set": 4}, [20], (None, None)),
            ({"rise": 6, "set": 18}, {"rise": None, "set": None}, [40], (18, 6)),
            ({"rise": 6, "set": 18}, {"rise": None, "set": None}, [-40], (None, None)),
        ):
            with self.subTest(expected=expected, altitudes=altitudes):
                with (
                    patch.object(p, "_find_rise_set_transit", side_effect=[sun_times, obj_times]),
                    patch.object(p, "_equatorial_to_horizontal", side_effect=[
                        (altitude, 0) for altitude in altitudes
                    ]),
                ):
                    self.assertEqual(
                        self.provider._find_visibility_window(0, 0, self.jd), expected
                    )

    def test_greenwich_has_a_real_saturn_window_across_midnight(self):
        ra, dec = coordinates("saturn", self.jd)
        start, end = self.provider._find_visibility_window(ra, dec, self.jd)
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertGreater(start, end)
        sun_ra, sun_dec = coordinates("sun", self.jd)
        jd0 = math.floor(self.jd - 0.5) + 0.5
        duration = (end - start) % 24
        for fraction in (0.1, 0.5, 0.9):
            when = jd0 + (start + duration * fraction) / 24
            altitude, _ = p._equatorial_to_horizontal(ra, dec, 51.5, 0, when)
            sun_altitude, _ = p._equatorial_to_horizontal(sun_ra, sun_dec, 51.5, 0, when)
            self.assertGreater(altitude, -0.5667)
            self.assertLess(sun_altitude, -12)
