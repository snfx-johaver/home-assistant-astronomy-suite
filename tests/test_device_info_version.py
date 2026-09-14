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

The perturbation control, which this module runs
------------------------------------------------
Perturbing ``manifest.json`` alone does **not** turn this suite red, and that
is correct rather than a gap: once the version is single-sourced the platforms
follow the manifest, so bumping it is a release, not a defect. To exercise the
manifest comparison you have to restore the counterfactual it guards against --
replace ``INTEGRATION_VERSION`` with a hand-synced literal at every site, *then*
bump the manifest. In that configuration
``test_all_platforms_report_the_same_version`` passes (ten identically stale
values do agree) while ``test_every_platform_reports_the_manifest_version``
fails, which is the whole reason both assertions exist.

That paragraph used to be the whole of it -- a description of a control nobody
ran. A described control is worth nothing: it makes exactly the same claim
whether or not the assertion it describes still works, and an assertion that
cannot fail is indistinguishable from one that passes. ``PerturbationControl``
below now *performs* it, on a throwaway copy of the component, in a subprocess.

Both halves are asserted, because either alone would be satisfiable by a broken
instrument. A run that reported failure for any reason at all -- a syntax error
in the rewritten copy, a missing fixture, an import that never resolved -- would
satisfy "the manifest assertion fails" while proving nothing about the
assertion. So the control requires the *specific* pairing the design predicts:
the agreement test green and the manifest test red, in the same run, over a full
complement of discovered platforms. Only that combination distinguishes a
working assertion from a broken harness.

``INTEGRATION_VERSION`` is also resolved once at ``const`` import and never
re-read, so a manifest-perturbation test written against the *fixed* code is
order-dependent: perturb before ``const`` is imported and the platforms follow
the new value, perturb after and they keep the old one and go red. That is
correct for production -- editing a manifest under a running Home Assistant
should not retroactively change what entities report -- but it will look like
flakiness to anyone who writes such a test without knowing. The subprocess
sidesteps it entirely: the perturbed tree is complete before any component
module is imported, so there is no ordering to get wrong.
"""

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def _perturbed_component(destination):
    """Rebuild the pre-fix defect in a copy: hand-synced literals, stale.

    Two edits, in this order, because each alone is insufficient:

    1. Replace every ``INTEGRATION_VERSION`` reference in a ``sw_version``
       position with a *literal* holding the manifest's current value. This
       un-does the single-sourcing -- the platforms stop tracking the manifest
       and start carrying their own copies, which is precisely the pre-fix
       arrangement.
    2. Bump ``manifest.json``. Now the literals are stale.

    Doing only (1) leaves the literals correct, so nothing goes red and the
    control would conclude the assertion works when it had never been tested.
    Doing only (2) leaves the platforms following the manifest, so they move
    with it and again nothing goes red. The defect exists only in the
    conjunction, which is exactly why it survived in production: each half
    looks harmless.

    Returns the stale version the literals were pinned to, so the caller can
    assert the failure names it rather than accepting any failure at all.
    """
    shutil.copytree(COMPONENT_DIR, destination, dirs_exist_ok=True)

    stale = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))["version"]

    rewritten = 0
    for path in sorted(destination.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if '"sw_version": INTEGRATION_VERSION' not in source:
            continue
        rewritten += source.count('"sw_version": INTEGRATION_VERSION')
        path.write_text(
            source.replace(
                '"sw_version": INTEGRATION_VERSION',
                f'"sw_version": "{stale}"',
            ),
            encoding="utf-8",
        )

    if rewritten < KNOWN_PAYLOAD_COUNT:
        # A rewrite that matched nothing would produce an unperturbed copy, and
        # an unperturbed copy passes -- which the control would read as "the
        # assertion did not fire". That is the broken-instrument reading of a
        # green result, so refuse it here where the cause is still visible.
        raise AssertionError(
            f"perturbation rewrote only {rewritten} sw_version sites; "
            f"expected at least {KNOWN_PAYLOAD_COUNT}. The source spelling "
            "has changed and this control is no longer perturbing anything."
        )

    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    major, minor, patch = (int(part) for part in stale.split("."))
    manifest["version"] = f"{major}.{minor}.{patch + 1}"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return stale, manifest["version"]


class PerturbationControl(unittest.TestCase):
    """Run the counterfactual this module used to only describe.

    The assertions here are about *this test file*, not about the component:
    they establish that ``test_every_platform_reports_the_manifest_version``
    can still fail. Nothing else in the suite can establish that, because the
    tree it runs against does not have the defect.
    """

    def test_hand_synced_literals_are_caught_by_the_manifest_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            component = Path(tmp) / "nasa_astronomy"
            stale, bumped = _perturbed_component(component)

            environment = dict(os.environ)
            environment["NASA_ASTRONOMY_COMPONENT_DIR"] = str(component)
            # `manifest_version()` in the child must read the perturbed
            # manifest, and the modules it imports must come from the perturbed
            # tree. Both follow from the one variable, so there is no way for
            # the child to half-perturb itself.
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "-v",
                    "test_device_info_version.DeviceInfoVersionTests",
                ],
                cwd=str(Path(__file__).resolve().parent),
                env=environment,
                capture_output=True,
                text=True,
            )

            report = completed.stderr

            # The pairing is the whole assertion. A child that failed for an
            # unrelated reason -- a syntax error in the rewritten copy, an
            # import that never resolved, a fixture that vanished -- would
            # produce a red run that says nothing about the assertion under
            # test. Requiring one specific test red *and* another specific test
            # green in the same run excludes that: a broken harness cannot
            # selectively pass the agreement check.
            self.assertIn(
                "test_all_platforms_report_the_same_version",
                report,
                f"the child did not run the expected tests:\n{report}",
            )
            # `unittest -v` prints the test id, then the docstring summary on
            # the FOLLOWING line, then the verdict -- so the verdict is not on
            # the name's line and a single-line regex silently never matches.
            # `[\s\S]*?` is a non-greedy any-character span including newlines;
            # `.` would not cross the line break even with DOTALL off, which is
            # exactly the trap. Anchoring on the next test id keeps the span
            # from running past this result into a later one.
            self.assertRegex(
                report,
                r"test_all_platforms_report_the_same_version[\s\S]*?\.\.\. ok",
                "ten identically stale literals must still AGREE -- if this "
                "went red the perturbation broke something other than the "
                f"version, and the control proves nothing:\n{report}",
            )
            self.assertRegex(
                report,
                r"test_every_platform_reports_the_manifest_version[\s\S]*?\.\.\. FAIL",
                "the manifest comparison did NOT catch hand-synced stale "
                f"literals; it is no longer load-bearing:\n{report}",
            )
            # Name the values, so the failure is the drift this guards against
            # and not some other difference that happens to be red.
            self.assertIn(bumped, report, f"failure did not cite the manifest version:\n{report}")
            self.assertIn(stale, report, f"failure did not cite the stale literal:\n{report}")

    def test_the_unperturbed_tree_passes_the_same_child_run(self):
        """Must-find control for the control.

        The test above reads a FAIL out of a subprocess. A subprocess that
        failed *unconditionally* -- wrong cwd, unimportable module, missing
        harness -- would satisfy it while testing nothing, and would look
        identical in the log. Run the same child against the untouched tree and
        require green. Together the two pin the child from both sides: red only
        when the defect is present, green when it is not.
        """
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "test_device_info_version.DeviceInfoVersionTests",
            ],
            cwd=str(Path(__file__).resolve().parent),
            env={k: v for k, v in os.environ.items() if k != "NASA_ASTRONOMY_COMPONENT_DIR"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "the unperturbed tree must pass; if this is red the subprocess "
            f"fails for reasons unrelated to the perturbation:\n{completed.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
