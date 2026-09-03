"""Regression tests for the ``sw_version`` drift defect.

Run with: python -m unittest discover -s tests -p "test_*.py"

Every platform in this integration registers its entities against the *same*
device -- ``{(DOMAIN, entry_id)}`` -- and each one supplies its own
``device_info`` dict. Home Assistant therefore receives one device with N
version claims, and displays whichever platform registered last. Before the
fix those claims were three different hardcoded literals (``1.7.0``,
``1.8.0``, ``1.8.1``) while ``manifest.json`` said ``1.11.1``, so the displayed
version was both arbitrary and wrong.

What this file asserts, and why it is shaped this way
----------------------------------------------------
The obvious test -- grep the sources for hardcoded version strings -- measures
the *text*, not the program. It passes the moment someone writes the literal
in a comment, and it fails a fix that documents what it removed. So these
tests construct the real ``device_info`` payloads by instantiating the real
entity classes, and assert over the payloads.

Two invariants, and both are needed:

``test_all_platforms_report_the_same_version``
    catches one platform drifting away from the others.

``test_every_platform_reports_the_manifest_version``
    catches *all* platforms drifting away from the release together, which is
    what happens if someone hand-syncs the literals instead of single-sourcing
    them. Agreement on its own is a weak invariant -- ten identically stale
    values satisfy it. The manifest comparison is what makes agreement mean
    something.

The platforms are *discovered*, not listed. The failure mode being guarded
against is precisely a module somebody forgot about, so a hand-written list
would have the same blind spot as the defect.

A note on running the perturbation control
------------------------------------------
Perturbing ``manifest.json`` alone does **not** turn this suite red, and that
is correct rather than a gap: once the version is single-sourced the platforms
follow the manifest, so bumping it is a release, not a defect. To exercise the
manifest comparison you have to restore the counterfactual it guards against --
replace ``INTEGRATION_VERSION`` with a hand-synced literal at every site, *then*
bump the manifest. In that configuration
``test_all_platforms_report_the_same_version`` passes (ten identically stale
values do agree) while ``test_every_platform_reports_the_manifest_version``
fails, which is the whole reason both assertions exist.
"""

import ast
import json
import unittest
from pathlib import Path

from harness import COMPONENT_DIR, load_component_module

MANIFEST_PATH = COMPONENT_DIR / "manifest.json"
RELEASE_VERSION_PATH = Path(__file__).resolve().parent.parent / "version.json"

# Floors, not exact counts: a fifth platform should not break the suite, but a
# discovery walk that silently finds nothing must. Without these, every
# assertion below would pass vacuously over an empty list.
KNOWN_MODULE_COUNT = 4
KNOWN_PAYLOAD_COUNT = 10


def manifest_version():
    """The one version a release actually updates."""
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["version"]


class _Anything:
    """A stand-in for whatever an entity constructor is handed.

    Constructors take coordinators, config entries, catalog keys and indices,
    and do small things to them -- attribute access, f-string interpolation,
    ``index + 1``, ``str.capitalize()``, membership in a set. This absorbs all
    of that so the test can build entities generically instead of hardcoding a
    call signature per class, which would reintroduce the hand-listing this
    file exists to avoid.
    """

    def __init__(self, label="stub"):
        object.__setattr__(self, "_label", label)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _Anything(f"{self._label}.{name}")

    def __call__(self, *args, **kwargs):
        return _Anything(f"{self._label}()")

    def __getitem__(self, item):
        return _Anything(f"{self._label}[{item!r}]")

    def __add__(self, other):
        return _Anything(f"{self._label}+{other!r}")

    __radd__ = __add__

    def __str__(self):
        return self._label

    __repr__ = __str__

    def __format__(self, spec):
        return format(self._label, spec)

    def __hash__(self):
        return hash(self._label)

    def __eq__(self, other):
        return isinstance(other, _Anything) and str(other) == self._label

    def __bool__(self):
        return True


# The platforms take the config entry by two different spellings: ``camera.py``
# and ``sensor.py`` receive the ``entry`` object and read ``entry.entry_id``,
# while ``sensor_deepsky.py`` and ``sensor_ephemeris.py`` receive the id
# directly -- their setup functions pass ``entry_id=entry.entry_id``. Those are
# the same value at runtime, so the placeholders have to be the same value too;
# otherwise the identity control below would fail on a difference that exists
# only in the test's own scaffolding.
ENTRY_ID = _Anything("entry_id")
CONFIG_ENTRY = _Anything("entry")
CONFIG_ENTRY.entry_id = ENTRY_ID

CONFIG_ENTRY_PARAMETERS = {
    "entry": CONFIG_ENTRY,
    "config_entry": CONFIG_ENTRY,
    "entry_id": ENTRY_ID,
}


def _module_ref(path):
    """Map a source path to the ``(name, subpackage)`` the harness wants."""
    relative = path.relative_to(COMPONENT_DIR)
    subpackage = "/".join(relative.parts[:-1]) or None
    return relative.stem, subpackage


def _builds_device_info(class_node):
    """True if this class assigns ``_attr_device_info`` or defines ``device_info``.

    Both spellings register a device with Home Assistant, so both count. Walking
    the AST rather than importing first means a module that fails to import is
    reported as a failure instead of quietly contributing nothing.
    """
    for node in ast.walk(class_node):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "device_info" and node is not class_node:
                return True
            continue
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr in (
                "_attr_device_info",
                "device_info",
            ):
                return True
    return False


def discover_device_info_classes():
    """Every class in the component that registers a device, found by walking source."""
    found = []
    for path in sorted(COMPONENT_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _builds_device_info(node):
                found.append((path, node.name))
    return found


def _construct(cls):
    """Instantiate an entity class with placeholder arguments."""
    import inspect

    signature = inspect.signature(cls.__init__)
    args = []
    kwargs = {}
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.default is not inspect.Parameter.empty:
            continue  # let the real default stand
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        value = CONFIG_ENTRY_PARAMETERS.get(name, _Anything(name))
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            kwargs[name] = value
        else:
            args.append(value)
    return cls(*args, **kwargs)


def collect_device_info_payloads():
    """Build the real ``device_info`` dict from every platform that produces one.

    Returns ``(payloads, errors)`` where ``payloads`` is a list of
    ``(label, dict)``. Construction failures are returned rather than skipped:
    a platform that cannot be exercised is exactly the platform whose version
    nobody is checking.
    """
    payloads = []
    errors = []
    for path, class_name in discover_device_info_classes():
        label = f"{path.relative_to(COMPONENT_DIR).as_posix()}::{class_name}"
        name, subpackage = _module_ref(path)
        try:
            module = load_component_module(name, subpackage=subpackage)
            entity = _construct(getattr(module, class_name))
            payload = getattr(entity, "_attr_device_info", None)
            if not isinstance(payload, dict):
                payload = getattr(entity, "device_info", None)
            if not isinstance(payload, dict):
                raise TypeError(f"device_info was {payload!r}, not a dict")
        except Exception as err:  # noqa: BLE001 - reported, never swallowed
            errors.append(f"{label}: {type(err).__name__}: {err}")
            continue
        payloads.append((label, payload))
    return payloads, errors


PAYLOADS, ERRORS = collect_device_info_payloads()


class DeviceInfoDiscoveryTests(unittest.TestCase):
    """The tests below are only meaningful if discovery actually found things."""

    def test_every_discovered_platform_could_be_constructed(self):
        self.assertEqual(ERRORS, [], "device_info platforms failed to construct")

    def test_discovery_is_not_vacuous(self):
        """A floor on what must be found, so nothing below passes over an empty list.

        Four modules, ten payloads at the time of writing: camera 3, sensor 4,
        sensor_deepsky 2, sensor_ephemeris 1. Asserted as a minimum so adding a
        platform does not fail the suite, but deleting the discovery walk does.
        """
        modules = {label.split("::")[0] for label, _ in PAYLOADS}
        self.assertGreaterEqual(len(modules), KNOWN_MODULE_COUNT, sorted(modules))
        self.assertGreaterEqual(len(PAYLOADS), KNOWN_PAYLOAD_COUNT, sorted(
            label for label, _ in PAYLOADS
        ))


class DeviceInfoVersionTests(unittest.TestCase):
    """One device, so there must be exactly one version, and it must be the release."""

    def _versions(self):
        return {label: payload.get("sw_version") for label, payload in PAYLOADS}

    def test_every_device_info_carries_a_version(self):
        """A device registration that omits the version is the fifth-platform failure.

        Checked on constructed payloads rather than on source text, so it holds
        however the dict is built.
        """
        missing = [label for label, version in self._versions().items() if not version]
        self.assertEqual(missing, [], "device_info without an sw_version")

    def test_all_platforms_report_the_same_version(self):
        """Divergence between platforms.

        Before the fix this reported three distinct values for one device, and
        which one Home Assistant displayed depended on platform setup order.
        """
        versions = self._versions()
        distinct = sorted(set(versions.values()))
        self.assertEqual(
            len(distinct),
            1,
            f"one device is claiming {len(distinct)} versions {distinct}: {versions}",
        )

    def test_every_platform_reports_the_manifest_version(self):
        """The load-bearing assertion: platforms must track the release.

        ``test_all_platforms_report_the_same_version`` alone is satisfied by ten
        identically stale literals. This is the one that stays red in that case,
        because ``manifest.json`` is the only version a release updates.
        """
        expected = manifest_version()
        wrong = {
            label: version
            for label, version in self._versions().items()
            if version != expected
        }
        self.assertEqual(wrong, {}, f"manifest.json says {expected!r}")


class DeviceIdentityTests(unittest.TestCase):
    """Control: these hold before and after the fix.

    They exist so a reviewer can see the suite discriminating rather than being
    uniformly red, and they establish the premise that makes conflicting
    versions a defect at all -- every platform really is describing one device.
    """

    def test_manifest_version_is_a_release_version(self):
        version = manifest_version()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_manifest_agrees_with_the_repo_release_version(self):
        """``manifest.json`` must be the release, not just internally consistent.

        Everything above compares the platforms against ``manifest.json``, which
        the fix now derives them from -- so on its own that comparison cannot
        tell you the manifest itself is current. ``version.json`` is written by
        ``scripts/bump_version.py`` from a separate code path, so agreeing with
        it is independent evidence that what the platforms report really is the
        released version.
        """
        with RELEASE_VERSION_PATH.open(encoding="utf-8") as handle:
            release = json.load(handle)
        self.assertEqual(manifest_version(), release["integration"])

    def test_every_platform_registers_the_same_device(self):
        """Same identifiers, name, manufacturer and model across all platforms.

        If these ever diverge the versions are allowed to differ too, because
        they would no longer be describing one device -- so this is the premise
        the version assertions rest on, not decoration.
        """
        for field in ("identifiers", "name", "manufacturer", "model"):
            with self.subTest(field=field):
                claims = {label: payload.get(field) for label, payload in PAYLOADS}
                distinct = {repr(value) for value in claims.values()}
                self.assertEqual(len(distinct), 1, f"{field} differs: {claims}")


if __name__ == "__main__":
    unittest.main()
