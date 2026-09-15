"""Mechanical coverage checks for the bundled Lovelace dashboard."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "lovelace" / "astronomy-dashboard.yaml"
INTEGRATION = ROOT / "custom_components" / "nasa_astronomy"
CARD_SOURCES = (
    ROOT / "www" / "community" / "astronomy-cards" / "astronomy-cards.js",
    ROOT / "www" / "community" / "astronomy-cards" / "deepsky-cards.js",
)


def _assignment_value(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"{name} was not found in {path.relative_to(ROOT)}")


def _assignment_dict_keys(path: Path, name: str) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        target = None
        value = None
        if isinstance(node, ast.Assign):
            if any(isinstance(item, ast.Name) and item.id == name for item in node.targets):
                target = name
                value = node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                target = name
                value = node.value
        if target and isinstance(value, ast.List):
            keys = []
            for item in value.elts:
                assert isinstance(item, ast.Dict)
                values = {
                    ast.literal_eval(key): child
                    for key, child in zip(item.keys, item.values)
                    if key is not None
                }
                keys.append(ast.literal_eval(values["key"]))
            return keys
    raise AssertionError(f"{name} was not found in {path.relative_to(ROOT)}")


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.lower())).strip("_")


def _dashboard_strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _dashboard_strings(key)
            yield from _dashboard_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _dashboard_strings(child)
    elif isinstance(value, str):
        yield value


def _custom_card_types() -> set[str]:
    pattern = re.compile(r'(?:registerCustomCard\(|type:\s*)"([^"]+-card)"')
    return {
        match.group(1)
        for source in CARD_SOURCES
        for match in pattern.finditer(source.read_text(encoding="utf-8"))
    }


def _core_entities() -> set[str]:
    sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
    tree = ast.parse(sensor_source)
    descriptions = None
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "SENSOR_DESCRIPTIONS":
                descriptions = node.value
                break
    assert isinstance(descriptions, ast.List)

    sensors = set()
    for call in descriptions.elts:
        assert isinstance(call, ast.Call)
        name_keyword = next(keyword for keyword in call.keywords if keyword.arg == "name")
        sensors.add(f"sensor.astronomy_space_suite_{_slug(ast.literal_eval(name_keyword.value))}")

    sensors.update(
        f"sensor.astronomy_space_suite_rocket_launch_{index}" for index in range(1, 6)
    )
    sensors.update(
        {
            "sensor.astronomy_space_suite_iss_position",
            "sensor.astronomy_space_suite_planetary_kp_index",
        }
    )

    cameras = {
        "camera.astronomy_space_suite_apod_image",
        "camera.astronomy_space_suite_epic_earth",
        "camera.astronomy_space_suite_goes_16_earth",
        "camera.astronomy_space_suite_goes_18_earth",
        "camera.astronomy_space_suite_himawari_8_earth",
        "camera.astronomy_space_suite_sdo_sun",
        "camera.astronomy_space_suite_soho_sun",
    }
    return sensors | cameras


def _ephemeris_entities() -> set[str]:
    source = INTEGRATION / "sensor_ephemeris.py"
    sun = _assignment_dict_keys(source, "SUN_SENSORS")
    moon = _assignment_dict_keys(source, "MOON_SENSORS")
    planets = _assignment_dict_keys(source, "PLANET_SENSORS")
    sky = _assignment_dict_keys(source, "SKY_SENSORS")

    entities = {
        f"sensor.nasa_astronomy_ephemeris_sun_{key}" for key in sun
    }
    entities.update(
        f"sensor.nasa_astronomy_ephemeris_moon_{key}" for key in moon
    )
    entities.update(
        f"sensor.nasa_astronomy_ephemeris_{body}_{key}"
        for body in ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune")
        for key in planets
    )
    entities.update(
        f"sensor.nasa_astronomy_ephemeris_sky_{key}" for key in sky
    )
    return entities


def _deepsky_entities() -> set[str]:
    source = INTEGRATION / "sensor_deepsky.py"
    catalog = _assignment_value(source, "DSO_CATALOG")
    sensor_keys = _assignment_dict_keys(source, "DSO_OBJECT_SENSORS")
    entities = {"sensor.nasa_astronomy_deepsky_best_tonight"}
    entities.update(
        f"sensor.nasa_astronomy_deepsky_{_slug(name)}_{key}"
        for name, *_ in catalog
        for key in sensor_keys
    )
    return entities


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.dashboard = yaml.safe_load(DASHBOARD.read_text(encoding="utf-8"))

    def test_dashboard_yaml_is_valid_and_has_unique_paths(self):
        self.assertEqual(self.dashboard["title"], "Astronomy Space Suite")
        self.assertGreaterEqual(len(self.dashboard["views"]), 8)
        paths = [view["path"] for view in self.dashboard["views"]]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(all(view.get("type") == "sections" for view in self.dashboard["views"]))

    def test_every_registered_custom_card_is_represented(self):
        strings = set(_dashboard_strings(self.dashboard))
        configured = {
            value.removeprefix("custom:")
            for value in strings
            if value.startswith("custom:")
        }
        self.assertEqual(configured, _custom_card_types())
        self.assertIn("dso-yard-map-card", configured)
        self.assertIn("dso-dome-card", configured)

    def test_every_integration_entity_is_covered(self):
        configured = {
            value
            for value in _dashboard_strings(self.dashboard)
            if value.startswith(("sensor.", "camera.", "update."))
        }
        expected = _core_entities() | _ephemeris_entities() | _deepsky_entities()
        missing = expected - configured
        self.assertFalse(
            missing,
            f"Dashboard is missing {len(missing)} entities: {sorted(missing)}",
        )
        self.assertEqual(len(expected), 268)

    def test_dashboard_does_not_reference_unknown_astronomy_entities(self):
        configured = {
            value
            for value in _dashboard_strings(self.dashboard)
            if value.startswith(
                (
                    "sensor.astronomy_space_suite_",
                    "camera.astronomy_space_suite_",
                    "sensor.nasa_astronomy_",
                )
            )
            and value != "sensor.astronomy_space_suite_rocket_launch"
        }
        expected = _core_entities() | _ephemeris_entities() | _deepsky_entities()
        self.assertLessEqual(configured, expected)

    def test_dashboard_is_isolated_and_external_entities_are_allowlisted(self):
        self.assertNotIn("resources", self.dashboard)
        self.assertNotIn("theme", self.dashboard)
        configured = {
            value
            for value in _dashboard_strings(self.dashboard)
            if value.startswith(("sensor.", "camera.", "sun.", "update."))
        }
        integration_entities = _core_entities() | _ephemeris_entities() | _deepsky_entities()
        entity_prefixes = {"sensor.astronomy_space_suite_rocket_launch"}
        external = configured - integration_entities - entity_prefixes
        self.assertEqual(external, {"sun.sun", "sensor.moon_phase"})


if __name__ == "__main__":
    unittest.main()
