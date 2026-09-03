"""Regression tests for the deep-sky Julian Date timezone defect.

Run with: python -m unittest discover -s tests -p "test_*.py"

``DeepSkyProvider.compute_all`` samples the clock with
``datetime.now(timezone.utc).astimezone()``, which yields a tz-aware datetime
in the system's LOCAL zone. ``_julian_date`` then read ``dt.year``/``dt.hour``
and friends straight off that object and treated the local wall-clock fields
as though they were UTC, never inspecting ``dt.tzinfo``. Under CEST (UTC+2)
every Julian Date came out two hours ahead, which shifted local sidereal time
by ~2 sidereal hours, the hour angle by ~30 degrees, and every object's
altitude and azimuth with it.

The load-bearing assertion is ``test_same_instant_in_another_timezone_matches``:
one instant must produce one Julian Date regardless of which timezone it is
expressed in. That test fails against the pre-fix function and passes after.
"""

import unittest
from datetime import datetime, timedelta, timezone

from harness import load_component_module

sensor_deepsky = load_component_module("sensor_deepsky")
openastronomy_ephemeris = load_component_module(
    "openastronomy_ephemeris", subpackage="providers"
)

_julian_date = sensor_deepsky._julian_date
_compute_alt_az = sensor_deepsky._compute_alt_az

# The canonical epoch: 2000-01-01 12:00:00 TT is Julian Date 2451545.0.
J2000 = 2451545.0
J2000_UTC = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

CEST = timezone(timedelta(hours=2))
CET = timezone(timedelta(hours=1))


class JulianDateTests(unittest.TestCase):
    """``_julian_date`` must depend on the instant, not on its wall clock."""

    def test_j2000_epoch_is_exact(self):
        self.assertEqual(_julian_date(J2000_UTC), J2000)

    def test_same_instant_in_another_timezone_matches(self):
        """The whole bug in one assertion.

        13:00 in UTC+1 is the same instant as 12:00 UTC, so it must produce the
        same Julian Date. Before the fix this returned 2451545.0416666665 --
        one hour, and therefore one hour of sidereal rotation, too far ahead.
        """
        same_instant = datetime(2000, 1, 1, 13, 0, 0, tzinfo=CET)
        self.assertEqual(same_instant, J2000_UTC)  # same instant by construction
        self.assertEqual(_julian_date(same_instant), J2000)
        self.assertEqual(_julian_date(same_instant), _julian_date(J2000_UTC))

    def test_cest_the_reported_symptom_timezone(self):
        """CEST is UTC+2, the offset the position error was reported under."""
        same_instant = datetime(2000, 1, 1, 14, 0, 0, tzinfo=CEST)
        self.assertEqual(same_instant, J2000_UTC)
        self.assertEqual(_julian_date(same_instant), J2000)

    def test_negative_offset_zone(self):
        """A zone behind UTC, to prove the fix is not sign-specific."""
        same_instant = datetime(2000, 1, 1, 7, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(same_instant, J2000_UTC)
        self.assertEqual(_julian_date(same_instant), J2000)

    def test_offset_change_crossing_a_date_boundary(self):
        """The conversion must roll the calendar date, not just the hour."""
        same_instant = datetime(2000, 1, 2, 1, 0, 0, tzinfo=timezone(timedelta(hours=13)))
        self.assertEqual(same_instant, J2000_UTC)
        self.assertEqual(_julian_date(same_instant), J2000)

    def test_naive_datetime_is_still_read_as_utc(self):
        """Naive input keeps its existing meaning: fields are already UTC."""
        self.assertEqual(_julian_date(datetime(2000, 1, 1, 12, 0, 0)), J2000)

    def test_matches_the_known_correct_provider_implementation(self):
        """Parity with ``openastronomy_ephemeris._julian_day``.

        That module already normalised ``tzinfo`` before converting, which is
        why it was never affected. It is the in-repo reference for what this
        function should return.
        """
        reference = openastronomy_ephemeris._julian_day
        for moment in (
            J2000_UTC,
            datetime(2000, 1, 1, 13, 0, 0, tzinfo=CET),
            datetime(2024, 6, 21, 23, 45, 30, tzinfo=CEST),
            datetime(2024, 12, 31, 3, 15, 0, tzinfo=timezone(timedelta(hours=-8))),
            datetime(2024, 6, 21, 21, 45, 30),
        ):
            with self.subTest(moment=moment):
                self.assertAlmostEqual(_julian_date(moment), reference(moment), places=9)


class AltAzTimezoneTests(unittest.TestCase):
    """The user-visible symptom: positions must not depend on the clock's zone."""

    # M31, and a location where CEST applies.
    RA_HOURS = 0.712
    DEC_DEG = 41.27
    LAT = 55.6761
    LON = 12.5683

    def _alt_az(self, moment):
        return _compute_alt_az(self.RA_HOURS, self.DEC_DEG, self.LAT, self.LON, moment)

    def test_position_is_identical_for_one_instant_in_two_zones(self):
        utc_moment = datetime(2024, 9, 15, 22, 0, 0, tzinfo=timezone.utc)
        cest_moment = utc_moment.astimezone(CEST)
        self.assertEqual(utc_moment, cest_moment)
        self.assertEqual(self._alt_az(cest_moment), self._alt_az(utc_moment))

    def test_a_two_hour_offset_really_does_move_the_object(self):
        """Control: the assertion above is not vacuously true.

        Two genuinely different instants two hours apart give a materially
        different altitude. That is the size of the error the defect produced
        when it mistook a CEST wall clock for UTC.
        """
        utc_moment = datetime(2024, 9, 15, 22, 0, 0, tzinfo=timezone.utc)
        two_hours_later = utc_moment + timedelta(hours=2)
        alt_now, _ = self._alt_az(utc_moment)
        alt_later, _ = self._alt_az(two_hours_later)
        self.assertGreater(abs(alt_later - alt_now), 5.0)


if __name__ == "__main__":
    unittest.main()
