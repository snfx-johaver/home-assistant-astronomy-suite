"""OpenAstronomy Ephemeris Provider.

Local astronomical calculations for planetary positions, rise/set times,
twilight, and sky conditions. Uses simplified VSOP87 and Meeus algorithms.
No external API dependency — all calculations are performed locally.

Structured as a provider with caching and throttling to maintain
consistent behavior and avoid unnecessary recalculation.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Constants
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi
J2000 = 2451545.0
DAY_SECONDS = 86400

# Planetary orbital elements (J2000 epoch)
# a=semi-major axis(AU), e=eccentricity, i=inclination(deg),
# L=mean longitude(deg), wBar=longitude of perihelion(deg),
# Omega=longitude of ascending node(deg), daily=mean daily motion(deg/day)
ORBITAL_ELEMENTS: dict[str, dict[str, float]] = {
    "mercury": {"a": 0.387099, "e": 0.205635, "i": 7.005, "L": 252.251, "wBar": 77.458, "Omega": 48.331, "daily": 4.09233},
    "venus": {"a": 0.723332, "e": 0.006772, "i": 3.395, "L": 181.980, "wBar": 131.564, "Omega": 76.680, "daily": 1.60213},
    "earth": {"a": 1.000000, "e": 0.016709, "i": 0.000, "L": 100.464, "wBar": 102.937, "Omega": 0.0, "daily": 0.98561},
    "mars": {"a": 1.523688, "e": 0.093405, "i": 1.850, "L": 355.453, "wBar": 336.041, "Omega": 49.558, "daily": 0.52403},
    "jupiter": {"a": 5.202561, "e": 0.048498, "i": 1.303, "L": 34.404, "wBar": 14.331, "Omega": 100.464, "daily": 0.08309},
    "saturn": {"a": 9.554909, "e": 0.055548, "i": 2.489, "L": 49.944, "wBar": 92.432, "Omega": 113.666, "daily": 0.03346},
    "uranus": {"a": 19.21845, "e": 0.046381, "i": 0.773, "L": 313.232, "wBar": 170.964, "Omega": 74.006, "daily": 0.01173},
    "neptune": {"a": 30.11039, "e": 0.009456, "i": 1.770, "L": 304.880, "wBar": 44.971, "Omega": 131.784, "daily": 0.00598},
}

BODY_LIST = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]


class EphemerisCache:
    """Simple in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[datetime, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            timestamp, data = self._cache[key]
            if datetime.now(timezone.utc) - timestamp < timedelta(seconds=self._ttl):
                return data
        return None

    def set(self, key: str, data: Any) -> None:
        self._cache[key] = (datetime.now(timezone.utc), data)

    def clear(self) -> None:
        self._cache.clear()


class EphemerisThrottle:
    """Rate limiter — max N calls per hour."""

    def __init__(self, max_per_hour: int = 120):
        self._max = max_per_hour
        self._calls: list[datetime] = []

    def can_call(self) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        self._calls = [t for t in self._calls if t > cutoff]
        return len(self._calls) < self._max

    def record_call(self) -> None:
        self._calls.append(datetime.now(timezone.utc))


def _julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day Number."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    frac = (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    return jdn + frac


def _normalize_deg(deg: float) -> float:
    """Normalize angle to 0-360."""
    return deg % 360.0


def _solve_kepler(mean_anomaly_rad: float, eccentricity: float, iterations: int = 10) -> float:
    """Solve Kepler's equation via Newton-Raphson."""
    e_anom = mean_anomaly_rad
    for _ in range(iterations):
        de = (e_anom - eccentricity * math.sin(e_anom) - mean_anomaly_rad) / (1 - eccentricity * math.cos(e_anom))
        e_anom -= de
        if abs(de) < 1e-12:
            break
    return e_anom


def _obliquity(jd: float) -> float:
    """Mean obliquity of the ecliptic (degrees)."""
    t = (jd - J2000) / 36525.0
    return 23.4393 - 0.0130 * t


def _ecliptic_to_equatorial(lon_deg: float, lat_deg: float, obliq_deg: float) -> tuple[float, float]:
    """Convert ecliptic (lon, lat) to equatorial (RA, Dec) in degrees."""
    lon = lon_deg * DEG_TO_RAD
    lat = lat_deg * DEG_TO_RAD
    obliq = obliq_deg * DEG_TO_RAD

    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_obl = math.sin(obliq)
    cos_obl = math.cos(obliq)

    ra = math.atan2(sin_lon * cos_obl - math.tan(lat) * sin_obl, cos_lon)
    dec = math.asin(sin_lat * cos_obl + cos_lat * sin_obl * sin_lon)

    return _normalize_deg(ra * RAD_TO_DEG), dec * RAD_TO_DEG


def _equatorial_to_horizontal(ra_deg: float, dec_deg: float, lat: float, lon: float, jd: float) -> tuple[float, float]:
    """Convert equatorial (RA, Dec) to horizontal (altitude, azimuth) in degrees."""
    # Local sidereal time
    t = (jd - J2000) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - J2000) + 0.000387933 * t * t
    lst = _normalize_deg(gmst + lon)

    ha = _normalize_deg(lst - ra_deg) * DEG_TO_RAD
    dec = dec_deg * DEG_TO_RAD
    lat_rad = lat * DEG_TO_RAD

    sin_alt = math.sin(dec) * math.sin(lat_rad) + math.cos(dec) * math.cos(lat_rad) * math.cos(ha)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))

    cos_az = (math.sin(dec) - math.sin(alt) * math.sin(lat_rad)) / (math.cos(alt) * math.cos(lat_rad) + 1e-12)
    cos_az = max(-1.0, min(1.0, cos_az))
    az = math.acos(cos_az)
    if math.sin(ha) > 0:
        az = 2 * math.pi - az

    return alt * RAD_TO_DEG, az * RAD_TO_DEG


def _sun_position(jd: float) -> dict[str, float]:
    """Calculate heliocentric position of Earth, then geocentric Sun."""
    days = jd - J2000
    # Mean anomaly of the Sun
    m_deg = _normalize_deg(357.5291 + 0.98560028 * days)
    m_rad = m_deg * DEG_TO_RAD
    # Equation of center
    c = 1.9148 * math.sin(m_rad) + 0.0200 * math.sin(2 * m_rad) + 0.0003 * math.sin(3 * m_rad)
    # Sun's ecliptic longitude
    sun_lon = _normalize_deg(m_deg + c + 180.0 + 102.9372)
    # Sun's distance (AU)
    distance = 1.00014 - 0.01671 * math.cos(m_rad) - 0.00014 * math.cos(2 * m_rad)
    # Angular diameter (arcminutes)
    ang_diam = 2 * math.atan(0.00465047 / distance) * RAD_TO_DEG * 60

    return {
        "ecliptic_lon": sun_lon,
        "ecliptic_lat": 0.0,
        "distance_au": distance,
        "angular_diameter_arcmin": ang_diam,
        "mean_anomaly_deg": m_deg,
    }


def _moon_position(jd: float) -> dict[str, float]:
    """Simplified lunar position (Meeus, low accuracy)."""
    days = jd - J2000
    t = days / 36525.0

    # Fundamental arguments
    l0 = _normalize_deg(218.3165 + 13.176396 * days)  # Mean longitude
    m_sun = _normalize_deg(357.5291 + 0.98560028 * days)  # Sun mean anomaly
    m_moon = _normalize_deg(134.9634 + 13.064993 * days)  # Moon mean anomaly
    d = _normalize_deg(297.8502 + 12.190749 * days)  # Mean elongation
    f = _normalize_deg(93.2720 + 13.229350 * days)  # Argument of latitude

    m_sun_r = m_sun * DEG_TO_RAD
    m_moon_r = m_moon * DEG_TO_RAD
    d_r = d * DEG_TO_RAD
    f_r = f * DEG_TO_RAD

    # Ecliptic longitude (simplified)
    lon = l0 + 6.289 * math.sin(m_moon_r)
    lon += -1.274 * math.sin(2 * d_r - m_moon_r)
    lon += -0.658 * math.sin(2 * d_r)
    lon += 0.214 * math.sin(2 * m_moon_r)
    lon += -0.186 * math.sin(m_sun_r)
    lon += -0.114 * math.sin(2 * f_r)
    lon = _normalize_deg(lon)

    # Ecliptic latitude (simplified)
    lat = 5.128 * math.sin(f_r)
    lat += 0.281 * math.sin((m_moon_r + f_r))
    lat += -0.278 * math.sin((f_r - m_moon_r))
    lat += -0.173 * math.sin((2 * d_r - f_r))

    # Distance (km)
    dist = 385001 - 20905 * math.cos(m_moon_r)
    dist += -3699 * math.cos(2 * d_r - m_moon_r)
    dist += -2956 * math.cos(2 * d_r)

    # Angular diameter
    ang_diam = 2 * math.atan(1737.4 / dist) * RAD_TO_DEG * 60

    # Phase angle and illumination
    elongation = math.acos(
        max(-1.0, min(1.0, math.cos(d_r) * math.cos((lat * DEG_TO_RAD))))
    )
    phase_angle = 180.0 - elongation * RAD_TO_DEG
    illumination = (1 + math.cos(phase_angle * DEG_TO_RAD)) / 2.0 * 100

    return {
        "ecliptic_lon": lon,
        "ecliptic_lat": lat,
        "distance_km": dist,
        "angular_diameter_arcmin": ang_diam,
        "phase_angle": phase_angle,
        "illumination_pct": illumination,
        "mean_elongation_deg": d,
    }


def _planet_position(name: str, jd: float) -> dict[str, float]:
    """Calculate heliocentric position of a planet, convert to geocentric."""
    planet = ORBITAL_ELEMENTS[name]
    earth = ORBITAL_ELEMENTS["earth"]
    days = jd - J2000

    def _helio(elem: dict) -> tuple[float, float, float, float]:
        m_deg = _normalize_deg(elem["L"] + elem["daily"] * days - elem["wBar"])
        m_rad = m_deg * DEG_TO_RAD
        e_anom = _solve_kepler(m_rad, elem["e"])
        true_anom = 2 * math.atan2(
            math.sqrt(1 + elem["e"]) * math.sin(e_anom / 2),
            math.sqrt(1 - elem["e"]) * math.cos(e_anom / 2),
        )
        r = elem["a"] * (1 - elem["e"] * math.cos(e_anom))
        lon = true_anom + elem["wBar"] * DEG_TO_RAD
        # Simplified: assume ecliptic latitude ≈ 0 for planets (low inclination approximation)
        x = r * math.cos(lon)
        y = r * math.sin(lon)
        return x, y, r, _normalize_deg(lon * RAD_TO_DEG)

    # Earth heliocentric
    ex, ey, _, _ = _helio(earth)
    # Planet heliocentric
    px, py, pr, p_lon = _helio(planet)

    # Geocentric
    dx = px - ex
    dy = py - ey
    geo_dist = math.sqrt(dx * dx + dy * dy)
    geo_lon = _normalize_deg(math.atan2(dy, dx) * RAD_TO_DEG)

    # Phase angle (Sun-Planet-Earth)
    # Using law of cosines
    sun_dist = math.sqrt(ex * ex + ey * ey)
    cos_phase = (pr * pr + geo_dist * geo_dist - sun_dist * sun_dist) / (2 * pr * geo_dist + 1e-12)
    cos_phase = max(-1.0, min(1.0, cos_phase))
    phase_angle = math.acos(cos_phase) * RAD_TO_DEG

    # Illumination
    illumination = (1 + math.cos(phase_angle * DEG_TO_RAD)) / 2.0 * 100

    # Angular diameter (approximate radii in AU)
    radii_au = {
        "mercury": 1.63e-5, "venus": 4.05e-5, "mars": 2.27e-5,
        "jupiter": 4.67e-4, "saturn": 3.89e-4, "uranus": 1.70e-4, "neptune": 1.65e-4,
    }
    radius = radii_au.get(name, 1e-5)
    ang_diam = 2 * math.atan(radius / (geo_dist + 1e-12)) * RAD_TO_DEG * 3600  # arcseconds

    return {
        "ecliptic_lon": geo_lon,
        "ecliptic_lat": 0.0,  # Simplified
        "distance_au": geo_dist,
        "helio_distance_au": pr,
        "angular_diameter_arcsec": ang_diam,
        "phase_angle": phase_angle,
        "illumination_pct": illumination,
    }


def _find_rise_set_transit(
    ra_deg: float, dec_deg: float, lat: float, lon: float, jd: float, h0_deg: float = -0.5667
) -> dict[str, float | None]:
    """Approximate rise, transit, set times (as fractional hours UTC)."""
    # Local sidereal time at 0h UT
    jd0 = math.floor(jd - 0.5) + 0.5
    t = (jd0 - J2000) / 36525.0
    gmst0 = _normalize_deg(280.46061837 + 360.98564736629 * (jd0 - J2000))

    cos_h = (math.sin(h0_deg * DEG_TO_RAD) - math.sin(lat * DEG_TO_RAD) * math.sin(dec_deg * DEG_TO_RAD)) / (
        math.cos(lat * DEG_TO_RAD) * math.cos(dec_deg * DEG_TO_RAD) + 1e-12
    )

    if cos_h > 1:
        return {"rise": None, "transit": None, "set": None}  # Never rises
    if cos_h < -1:
        return {"rise": None, "transit": None, "set": None}  # Never sets (circumpolar)

    h_deg = math.acos(max(-1.0, min(1.0, cos_h))) * RAD_TO_DEG

    # Transit time
    transit = (ra_deg - lon - gmst0) / 360.0
    transit = transit % 1.0

    # Rise and set
    rise = transit - h_deg / 360.0
    set_time = transit + h_deg / 360.0

    rise = (rise % 1.0) * 24.0
    transit_h = (transit % 1.0) * 24.0
    set_h = (set_time % 1.0) * 24.0

    return {"rise": rise, "transit": transit_h, "set": set_h}


def _twilight_times(lat: float, lon: float, jd: float) -> dict[str, float | None]:
    """Calculate civil, nautical, astronomical twilight times."""
    sun = _sun_position(jd)
    obliq = _obliquity(jd)
    ra, dec = _ecliptic_to_equatorial(sun["ecliptic_lon"], 0.0, obliq)

    results = {}
    for name, h0 in [("civil", -6.0), ("nautical", -12.0), ("astronomical", -18.0)]:
        times = _find_rise_set_transit(ra, dec, lat, lon, jd, h0)
        results[f"{name}_dawn"] = times["rise"]
        results[f"{name}_dusk"] = times["set"]

    # Solar noon
    sun_times = _find_rise_set_transit(ra, dec, lat, lon, jd, -0.8333)
    results["solar_noon"] = sun_times["transit"]
    results["sunrise"] = sun_times["rise"]
    results["sunset"] = sun_times["set"]

    return results


def _local_sidereal_time(jd: float, lon: float) -> float:
    """Calculate local sidereal time in degrees."""
    t = (jd - J2000) / 36525.0
    gmst = _normalize_deg(280.46061837 + 360.98564736629 * (jd - J2000) + 0.000387933 * t * t)
    return _normalize_deg(gmst + lon)


def _equation_of_time(jd: float) -> float:
    """Equation of time in minutes."""
    days = jd - J2000
    m_deg = _normalize_deg(357.5291 + 0.98560028 * days)
    m_rad = m_deg * DEG_TO_RAD
    c = 1.9148 * math.sin(m_rad) + 0.0200 * math.sin(2 * m_rad)
    sun_lon = _normalize_deg(m_deg + c + 180.0 + 102.9372)
    obliq = _obliquity(jd)
    ra, _ = _ecliptic_to_equatorial(sun_lon, 0.0, obliq)
    # EoT = RA_mean_sun - RA_true_sun
    mean_lon = _normalize_deg(280.46646 + 0.98564736 * days)
    eot = mean_lon - ra
    if eot > 180:
        eot -= 360
    if eot < -180:
        eot += 360
    return eot * 4  # Convert degrees to minutes (1 degree = 4 minutes)


class OpenAstronomyEphemerisProvider:
    """Provider for astronomical ephemeris calculations.

    All calculations are local — no external API calls needed.
    Structured with caching and throttling for consistency.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        elevation: float = 0.0,
        update_interval: int = 3600,
        enabled_bodies: dict[str, bool] | None = None,
    ):
        self._lat = latitude
        self._lon = longitude
        self._elevation = elevation
        self._update_interval = update_interval
        self._enabled_bodies = enabled_bodies or {}
        self._cache = EphemerisCache(ttl_seconds=update_interval)
        self._throttle = EphemerisThrottle(max_per_hour=8)
        self._last_known: dict[str, dict] = {}
        self._last_success: dict[str, datetime] = {}
        self._stale_threshold = timedelta(hours=6)

    @property
    def enabled_bodies(self) -> list[str]:
        return [b for b in BODY_LIST if self._enabled_bodies.get(b, False)]

    def get_ephemeris(self, body: str) -> dict[str, Any] | None:
        """Get ephemeris data for a celestial body."""
        if body not in BODY_LIST:
            return None
        if not self._enabled_bodies.get(body, False):
            return None

        # Check cache
        cached = self._cache.get(body)
        if cached is not None:
            return cached

        # Throttle check
        if not self._throttle.can_call():
            _LOGGER.debug("Throttled: returning last known data for %s", body)
            return self._last_known.get(body)

        # Calculate
        try:
            self._throttle.record_call()
            data = self._calculate(body)
            self._cache.set(body, data)
            self._last_known[body] = data
            self._last_success[body] = datetime.now(timezone.utc)
            return data
        except Exception as err:
            _LOGGER.error("Ephemeris calculation failed for %s: %s", body, err)
            # Graceful degradation
            if body in self._last_known:
                age = datetime.now(timezone.utc) - self._last_success.get(body, datetime.min.replace(tzinfo=timezone.utc))
                if age < self._stale_threshold:
                    return self._last_known[body]
            return None

    def get_sky_conditions(self) -> dict[str, Any]:
        """Get general sky conditions."""
        cached = self._cache.get("_sky_conditions")
        if cached is not None:
            return cached

        now = datetime.now(timezone.utc)
        jd = _julian_day(now)

        sun = _sun_position(jd)
        obliq = _obliquity(jd)
        sun_ra, sun_dec = _ecliptic_to_equatorial(sun["ecliptic_lon"], 0.0, obliq)
        sun_alt, sun_az = _equatorial_to_horizontal(sun_ra, sun_dec, self._lat, self._lon, jd)

        moon_data = _moon_position(jd)
        moon_ra, moon_dec = _ecliptic_to_equatorial(moon_data["ecliptic_lon"], moon_data["ecliptic_lat"], obliq)
        moon_alt, _ = _equatorial_to_horizontal(moon_ra, moon_dec, self._lat, self._lon, jd)

        twilight = _twilight_times(self._lat, self._lon, jd)

        # Determine twilight phase
        if sun_alt > 0:
            twilight_phase = "day"
        elif sun_alt > -6:
            twilight_phase = "civil_twilight"
        elif sun_alt > -12:
            twilight_phase = "nautical_twilight"
        elif sun_alt > -18:
            twilight_phase = "astronomical_twilight"
        else:
            twilight_phase = "night"

        # Day/night length
        sunrise = twilight.get("sunrise")
        sunset = twilight.get("sunset")
        day_length = None
        night_length = None
        if sunrise is not None and sunset is not None:
            day_length = (sunset - sunrise) if sunset > sunrise else (24 - sunrise + sunset)
            night_length = 24.0 - day_length

        lst = _local_sidereal_time(jd, self._lon)
        eot = _equation_of_time(jd)

        data = {
            "twilight_phase": twilight_phase,
            "is_astronomical_night": sun_alt < -18,
            "is_sun_above_horizon": sun_alt > 0,
            "is_moon_above_horizon": moon_alt > 0,
            "day_length_hours": round(day_length, 4) if day_length else None,
            "night_length_hours": round(night_length, 4) if night_length else None,
            "local_sidereal_time_deg": round(lst, 4),
            "local_sidereal_time_hours": round(lst / 15.0, 4),
            "julian_date": round(jd, 6),
            "equation_of_time_minutes": round(eot, 2),
            "sun_altitude": round(sun_alt, 4),
            "moon_altitude": round(moon_alt, 4),
        }
        self._cache.set("_sky_conditions", data)
        return data

    def _calculate(self, body: str) -> dict[str, Any]:
        """Perform ephemeris calculation for a body."""
        now = datetime.now(timezone.utc)
        jd = _julian_day(now)
        obliq = _obliquity(jd)

        if body == "sun":
            return self._calc_sun(jd, obliq)
        elif body == "moon":
            return self._calc_moon(jd, obliq)
        else:
            return self._calc_planet(body, jd, obliq)

    def _calc_sun(self, jd: float, obliq: float) -> dict[str, Any]:
        sun = _sun_position(jd)
        ra, dec = _ecliptic_to_equatorial(sun["ecliptic_lon"], 0.0, obliq)
        alt, az = _equatorial_to_horizontal(ra, dec, self._lat, self._lon, jd)
        times = _find_rise_set_transit(ra, dec, self._lat, self._lon, jd, -0.8333)
        twilight = _twilight_times(self._lat, self._lon, jd)

        return {
            "altitude": round(alt, 4),
            "azimuth": round(az, 4),
            "right_ascension": round(ra, 4),
            "declination": round(dec, 4),
            "distance_au": round(sun["distance_au"], 6),
            "angular_diameter_arcmin": round(sun["angular_diameter_arcmin"], 2),
            "solar_noon": times["transit"],
            "rise": times["rise"],
            "set": times["set"],
            "civil_dawn": twilight.get("civil_dawn"),
            "civil_dusk": twilight.get("civil_dusk"),
            "nautical_dawn": twilight.get("nautical_dawn"),
            "nautical_dusk": twilight.get("nautical_dusk"),
            "astronomical_dawn": twilight.get("astronomical_dawn"),
            "astronomical_dusk": twilight.get("astronomical_dusk"),
        }

    def _calc_moon(self, jd: float, obliq: float) -> dict[str, Any]:
        moon = _moon_position(jd)
        ra, dec = _ecliptic_to_equatorial(moon["ecliptic_lon"], moon["ecliptic_lat"], obliq)
        alt, az = _equatorial_to_horizontal(ra, dec, self._lat, self._lon, jd)
        times = _find_rise_set_transit(ra, dec, self._lat, self._lon, jd, 0.125)

        # Next full/new moon (simplified — search forward)
        next_full = self._find_next_phase(jd, target_elongation=180.0)
        next_new = self._find_next_phase(jd, target_elongation=0.0)

        return {
            "altitude": round(alt, 4),
            "azimuth": round(az, 4),
            "right_ascension": round(ra, 4),
            "declination": round(dec, 4),
            "distance_km": round(moon["distance_km"], 1),
            "angular_diameter_arcmin": round(moon["angular_diameter_arcmin"], 2),
            "phase_angle": round(moon["phase_angle"], 2),
            "illumination_pct": round(moon["illumination_pct"], 1),
            "rise": times["rise"],
            "transit": times["transit"],
            "set": times["set"],
            "next_full_moon": next_full,
            "next_new_moon": next_new,
        }

    def _calc_planet(self, name: str, jd: float, obliq: float) -> dict[str, Any]:
        pos = _planet_position(name, jd)
        ra, dec = _ecliptic_to_equatorial(pos["ecliptic_lon"], pos["ecliptic_lat"], obliq)
        alt, az = _equatorial_to_horizontal(ra, dec, self._lat, self._lon, jd)
        times = _find_rise_set_transit(ra, dec, self._lat, self._lon, jd, -0.5667)

        # Visibility window: when planet is above horizon and sun is below -6°
        vis_start, vis_end = self._find_visibility_window(ra, dec, jd)

        return {
            "altitude": round(alt, 4),
            "azimuth": round(az, 4),
            "right_ascension": round(ra, 4),
            "declination": round(dec, 4),
            "distance_au": round(pos["distance_au"], 6),
            "illumination_pct": round(pos["illumination_pct"], 1),
            "phase_angle": round(pos["phase_angle"], 2),
            "angular_diameter_arcsec": round(pos["angular_diameter_arcsec"], 2),
            "rise": times["rise"],
            "transit": times["transit"],
            "set": times["set"],
            "visibility_start": vis_start,
            "visibility_end": vis_end,
        }

    def _find_next_phase(self, jd: float, target_elongation: float) -> str | None:
        """Find next lunar phase (simplified search)."""
        for day_offset in range(1, 35):
            test_jd = jd + day_offset
            moon = _moon_position(test_jd)
            elong = moon["mean_elongation_deg"]
            diff = abs(_normalize_deg(elong) - target_elongation)
            if diff < 5 or diff > 355:
                dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(days=test_jd - J2000)
                return dt.strftime("%Y-%m-%d")
        return None

    def _find_visibility_window(self, ra: float, dec: float, jd: float) -> tuple[float | None, float | None]:
        """Find when the object is above horizon during astronomical darkness."""
        sun = _sun_position(jd)
        obliq = _obliquity(jd)
        sun_ra, sun_dec = _ecliptic_to_equatorial(sun["ecliptic_lon"], 0.0, obliq)
        sun_times = _find_rise_set_transit(sun_ra, sun_dec, self._lat, self._lon, jd, -12.0)  # Nautical

        obj_times = _find_rise_set_transit(ra, dec, self._lat, self._lon, jd, -0.5667)

        if sun_times["set"] is None or obj_times["rise"] is None:
            return None, None

        # Visibility = overlap of (object above horizon) and (sun below -12°)
        dark_start = sun_times["set"]
        dark_end = sun_times["rise"] if sun_times["rise"] is not None else 24.0
        obj_rise = obj_times["rise"]
        obj_set = obj_times["set"] if obj_times["set"] is not None else 24.0

        vis_start = max(dark_start, obj_rise) if dark_start is not None else obj_rise
        vis_end = min(dark_end, obj_set) if dark_end is not None else obj_set

        if vis_start is not None and vis_end is not None and vis_end > vis_start:
            return round(vis_start, 2), round(vis_end, 2)
        return None, None
