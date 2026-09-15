"""Mechanical coverage checks for the bundled Lovelace dashboard."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

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


def _configured_entities(text: str) -> set[str]:
    return set(
        re.findall(r"\b(?:sensor|camera|sun|update)\.[a-z0-9_]+\b", text)
    )


def _configured_custom_cards(text: str) -> set[str]:
    return set(re.findall(r"\bcustom:([a-z0-9-]+-card)\b", text))


def _assert_yaml_subset_is_well_formed(test: unittest.TestCase, text: str) -> None:
    """Validate the indentation-based YAML subset used by the dashboard.

    The bundled dashboard intentionally uses only mappings, sequences, scalar
    values, comments, and one folded scalar. Keeping this validator in the
    standard library makes the Sensor Tests job accurately exercise its real
    dependency set instead of silently requiring PyYAML.
    """
    previous_indent = 0
    previous_content = ""
    seen_indents = {0}
    block_scalar_indent = None

    for line_number, line in enumerate(text.splitlines(), 1):
        test.assertNotIn("\t", line, f"tab indentation on line {line_number}")
        test.assertEqual(line.rstrip(), line, f"trailing whitespace on line {line_number}")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(stripped)
        if block_scalar_indent is not None:
            if indent >= block_scalar_indent:
                continue
            block_scalar_indent = None

        test.assertEqual(indent % 2, 0, f"odd indentation on line {line_number}")
        if indent > previous_indent:
            test.assertEqual(
                indent,
                previous_indent + 2,
                f"indentation jumps more than one level on line {line_number}",
            )
            test.assertTrue(
                previous_content.endswith(":")
                or previous_content.startswith("- ")
                or previous_content.endswith((">-", "|-", ">", "|")),
                f"unexpected indentation after line {line_number - 1}",
            )
            seen_indents.add(indent)
        elif indent < previous_indent:
            test.assertIn(indent, seen_indents, f"unknown dedent on line {line_number}")

        content = stripped
        if content.startswith("- "):
            payload = content[2:].strip()
            test.assertTrue(payload, f"empty sequence item on line {line_number}")
            if ":" in payload:
                key, _, _ = payload.partition(":")
                test.assertRegex(key, r"^[a-zA-Z0-9_-]+$")
        else:
            test.assertIn(":", content, f"mapping colon missing on line {line_number}")
            key, _, _ = content.partition(":")
            test.assertRegex(key, r"^[a-zA-Z0-9_-]+$")

        previous_indent = indent
        previous_content = content
        if content.endswith((">-", "|-", ">", "|")):
            block_scalar_indent = indent + 2


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
        "camera.astronomy_space_suite_meteosat_12_earth",
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
        self.dashboard = DASHBOARD.read_text(encoding="utf-8")

    def test_dashboard_yaml_is_valid_and_has_unique_paths(self):
        _assert_yaml_subset_is_well_formed(self, self.dashboard)
        self.assertRegex(self.dashboard, r"(?m)^title: Astronomy Space Suite$")
        paths = re.findall(r"(?m)^    path: ([a-z0-9-]+)$", self.dashboard)
        self.assertGreaterEqual(len(paths), 8)
        self.assertEqual(len(paths), len(set(paths)))
        view_types = re.findall(r"(?m)^    type: ([a-z0-9-]+)$", self.dashboard)
        self.assertEqual(view_types, ["sections"] * len(paths))

    def test_every_registered_custom_card_is_represented(self):
        configured = _configured_custom_cards(self.dashboard)
        self.assertEqual(configured, _custom_card_types())
        self.assertIn("dso-yard-map-card", configured)
        self.assertIn("dso-dome-card", configured)

    def test_every_integration_entity_is_covered(self):
        configured = _configured_entities(self.dashboard)
        expected = _core_entities() | _ephemeris_entities() | _deepsky_entities()
        missing = expected - configured
        self.assertFalse(
            missing,
            f"Dashboard is missing {len(missing)} entities: {sorted(missing)}",
        )
        self.assertEqual(len(expected), 269)

    def test_dashboard_does_not_reference_unknown_astronomy_entities(self):
        configured = {
            value
            for value in _configured_entities(self.dashboard)
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
        top_level_keys = re.findall(r"(?m)^([a-zA-Z0-9_-]+):", self.dashboard)
        self.assertEqual(top_level_keys, ["title", "views"])
        configured = _configured_entities(self.dashboard)
        integration_entities = _core_entities() | _ephemeris_entities() | _deepsky_entities()
        entity_prefixes = {"sensor.astronomy_space_suite_rocket_launch"}
        external = configured - integration_entities - entity_prefixes
        self.assertEqual(external, {"sun.sun", "sensor.moon_phase"})


if __name__ == "__main__":
    unittest.main()
