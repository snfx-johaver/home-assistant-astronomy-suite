"""The diagnostics report must measure the install, not restate its claims.

Three mechanisms report a version and none of them looks at the files a
browser receives. ``manifest.json`` is what a release wrote; ``sw_version`` is
that same claim read back; HACS's ``version_installed`` is a log of what HACS
itself did, so anything writing to the install directory by another route
leaves it saying "up to date" -- correct about its own history, wrong about
the artefact. A real install sat in exactly that state, and the only
instrument that ever caught it was reading the files over SMB.

So the thing under test is not "does a report exist" but "is what it prints a
function of the bytes on disk". Every test here mutates a fixture and asserts
the report follows.

On controls. This module is new, so running it against the previous commit
fails with ``ImportError`` for every test -- which measures nothing except
that the file is absent. The honest control is a discrimination matrix:
plausible wrong implementations, each of which must turn its own test red and
leave the others green. Those mutations are recorded in the pull request:
hashing the version instead of the bytes, dropping an entry from the deploy
list, normalising line endings before classifying, hardcoding the match flag,
and pointing the entry point at the wrong directory.
"""

import asyncio
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

from harness import load_component_module
from test_resource_registration import FakeHass

package_init = load_component_module("__init__")
diagnostics = load_component_module("diagnostics")

# Deliberately chosen so the three renderings the classifier must tell apart
# all appear, including a binary payload whose *signature contains CRLF* --
# the PNG magic number is 89 50 4E 47 0D 0A 1A 0A. A classifier that looked at
# line endings before checking for binary content would report a confident
# rendering for an image.
FIXTURE_CONTENT = {
    "astronomy-cards.js": b"console.log('a');\nconsole.log('b');\n",
    "deepsky-cards.js": b"console.log('c');\r\nconsole.log('d');\r\n",
    "world-map.png": b"\x89PNG\r\n\x1a\n" + bytes(16),
}
FIXTURE_DEFAULT = b"placeholder\n"


def write_fixture(root):
    """A miniature install: the package directory and the served directory.

    Content is keyed off ``DEPLOYED_FILENAMES`` rather than a list of its own,
    so a file added to the deploy still gets a fixture and the tests below
    keep covering it instead of quietly skipping it.
    """
    package_dir = Path(root) / "package"
    www_dir = Path(root) / "www"
    package_dir.mkdir()
    www_dir.mkdir()
    for filename in package_init.DEPLOYED_FILENAMES:
        payload = FIXTURE_CONTENT.get(filename, FIXTURE_DEFAULT)
        (package_dir / filename).write_bytes(payload)
        (www_dir / filename).write_bytes(payload)
    return package_dir, www_dir


class LineEndingClassifierTests(unittest.TestCase):
    """The provenance field, pinned on synthetic bytes.

    Not on the repository's own files: every one of them is LF, so a
    classifier that returned ``"lf"`` unconditionally would pass a sweep of
    the tree. The correct answer and a broken answer are the same value.
    """

    def test_the_classifier_distinguishes_the_renderings(self):
        cases = [
            (b"a\nb\n", "lf", "unix"),
            (b"a\r\nb\r\n", "crlf", "windows"),
            (b"a\r\nb\n", "mixed", "half-converted"),
            (b"abc", "none", "single line"),
            (b"", "none", "empty"),
        ]
        for payload, expected, label in cases:
            with self.subTest(label):
                self.assertEqual(diagnostics.line_endings(payload), expected)

    def test_a_binary_payload_is_not_given_a_rendering(self):
        """PNG's signature contains CRLF, so this is a real trap, not a hypothetical."""
        png = FIXTURE_CONTENT["world-map.png"]
        self.assertIn(b"\r\n", png, "fixture no longer exercises the trap")
        self.assertIsNone(diagnostics.line_endings(png))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.package_dir, self.www_dir = write_fixture(self._tmp.name)

    def report(self):
        return diagnostics.build_report(self.package_dir, self.www_dir, [])

    def test_the_report_covers_every_deployed_file(self):
        """Enumerated from the deploy list, so a fourth file cannot be forgotten."""
        self.assertEqual(
            set(self.report()["files"]),
            set(package_init.DEPLOYED_FILENAMES),
        )

    def test_the_digest_is_a_measurement_of_the_bytes(self):
        installed = self.report()["files"]["astronomy-cards.js"]["installed"]
        self.assertEqual(
            installed["sha256"],
            hashlib.sha256(FIXTURE_CONTENT["astronomy-cards.js"]).hexdigest(),
        )
        self.assertEqual(installed["bytes"], len(FIXTURE_CONTENT["astronomy-cards.js"]))

    def test_changing_one_byte_changes_the_reported_digest(self):
        """The property the whole report rests on: it follows the file."""
        before = self.report()["files"]["astronomy-cards.js"]["installed"]["sha256"]
        target = self.package_dir / "astronomy-cards.js"
        mutated = target.read_bytes().replace(b"console.log('a')", b"console.log('z')")
        self.assertNotEqual(mutated, target.read_bytes(), "MUTATION NO-OP - ABORT")
        target.write_bytes(mutated)
        after = self.report()["files"]["astronomy-cards.js"]["installed"]["sha256"]
        self.assertNotEqual(before, after)

    def test_the_report_records_the_rendering_of_each_file(self):
        """The evidence that distinguishes a HACS delivery from a hand-copy."""
        files = self.report()["files"]
        self.assertEqual(files["astronomy-cards.js"]["installed"]["line_endings"], "lf")
        self.assertEqual(files["deepsky-cards.js"]["installed"]["line_endings"], "crlf")
        self.assertIsNone(files["world-map.png"]["installed"]["line_endings"])

    def test_a_served_copy_that_differs_from_the_installed_one_is_flagged(self):
        """A browser gets the served copy, so disagreement is the whole point."""
        self.assertTrue(
            self.report()["files"]["astronomy-cards.js"]["served_matches_installed"]
        )
        (self.www_dir / "astronomy-cards.js").write_bytes(b"stale\n")
        self.assertFalse(
            self.report()["files"]["astronomy-cards.js"]["served_matches_installed"]
        )

    def test_a_missing_served_copy_is_reported_absent_and_not_a_match(self):
        (self.www_dir / "deepsky-cards.js").unlink()
        entry = self.report()["files"]["deepsky-cards.js"]
        self.assertFalse(entry["served"]["present"])
        self.assertFalse(entry["served_matches_installed"])

    def test_two_files_with_different_content_get_different_digests(self):
        """Guards the degenerate implementation that hashes one constant."""
        files = self.report()["files"]
        digests = {name: entry["installed"]["sha256"] for name, entry in files.items()}
        self.assertEqual(len(set(digests.values())), len(digests), digests)

    def test_the_report_states_the_manifest_version(self):
        """Non-vacuity.

        The version is the *claim*, and it stays correct under every mutation
        that breaks a measurement above. It is here so a reviewer can see the
        suite discriminating rather than going uniformly red.
        """
        manifest = self.package_dir.parent / "manifest.json"
        self.assertFalse(manifest.exists(), "fixture must not supply a manifest")
        self.assertEqual(
            self.report()["integration_version"], package_init.INTEGRATION_VERSION
        )


class DeployCoverageTests(unittest.TestCase):
    """The deploy list must be what the deploy actually does.

    ``DEPLOYED_FILENAMES`` exists so the report can enumerate instead of
    sampling, which only helps if the declaration cannot drift from the
    behaviour. This runs the real deploy and compares.
    """

    def test_the_declared_list_is_exactly_what_the_deploy_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            hass = FakeHass(tmp)
            package_init._deploy_cards_to_www(hass)
            written = {
                path.name
                for path in package_init.deployed_dir(hass).iterdir()
                if path.is_file()
            }
        self.assertEqual(written, set(package_init.DEPLOYED_FILENAMES))

    def test_the_deploy_wrote_something(self):
        """Non-vacuity: an empty directory would equal an empty declaration."""
        self.assertGreaterEqual(len(package_init.DEPLOYED_FILENAMES), 3)


class ReferencedAssetTests(unittest.TestCase):
    """The deploy list must satisfy what the bundles actually ask for.

    ``DEPLOYED_FILENAMES`` is a declaration, and the deploy and the report
    both read it -- so dropping an entry is self-consistent and neither of
    them would notice. The anchor has to come from outside the declaration.

    The bundles supply one: they request assets from their own served
    directory by URL, and anything they request that is not deployed is a 404
    in a user's browser. This is also the standing answer to why a
    half-megabyte image ships with an integration -- the astronomy bundle
    draws it.
    """

    ASSET_REF = re.compile(r"/local/community/astronomy-cards/([A-Za-z0-9._-]+)")

    def referenced(self):
        component_dir = Path(package_init.__file__).parent
        found = set()
        for bundle in sorted(component_dir.glob("*.js")):
            text = bundle.read_text(encoding="utf-8", errors="replace")
            found |= set(self.ASSET_REF.findall(text))
        return found - {path.name for path in component_dir.glob("*.js")}

    def test_every_asset_the_bundles_request_is_deployed(self):
        missing = self.referenced() - set(package_init.DEPLOYED_FILENAMES)
        self.assertFalse(
            missing,
            "%d asset(s) a card bundle loads from its own directory are never "
            "copied there, so they 404 in the browser: %s"
            % (len(missing), ", ".join(sorted(missing))),
        )

    def test_the_scan_found_a_reference(self):
        """Non-vacuity: an empty scan is a subset of anything."""
        self.assertGreaterEqual(len(self.referenced()), 1)


class WiringTests(unittest.TestCase):
    def test_the_entry_point_reads_the_directory_the_deploy_writes(self):
        """Catches a report that is correct about the wrong place.

        Reading one path and printing the answer for another is a confident
        wrong measurement, and it is invisible from inside the report.
        """
        with tempfile.TemporaryDirectory() as tmp:
            hass = FakeHass(tmp)
            package_init._deploy_cards_to_www(hass)
            report = asyncio.run(
                diagnostics.async_get_config_entry_diagnostics(hass, None)
            )
            expected = diagnostics.build_report(
                Path(package_init.__file__).parent,
                package_init.deployed_dir(hass),
                [
                    package_init.resource_url(hass, name)
                    for name in package_init.BUNDLE_FILENAMES
                ],
            )
        self.assertEqual(report, expected)
        for name, entry in report["files"].items():
            with self.subTest(name):
                self.assertTrue(entry["served"]["present"])
                self.assertTrue(entry["served_matches_installed"])

    def test_the_report_lists_every_resource_url_the_integration_registers(self):
        """Discovered from the package, so a third bundle cannot be omitted.

        The URLs and the report have to describe *one* install. Both are now
        functions of ``hass``, so building them from separate directories
        would compare the keys of one set of bytes against the report of
        another and call the disagreement a defect.
        """
        with tempfile.TemporaryDirectory() as tmp:
            hass = FakeHass(tmp)
            package_init._deploy_cards_to_www(hass)
            registered = {
                package_init.resource_url(hass, name)
                for name in package_init.BUNDLE_FILENAMES
            }
            report = asyncio.run(
                diagnostics.async_get_config_entry_diagnostics(hass, None)
            )
        self.assertGreaterEqual(len(registered), 2, registered)
        self.assertEqual(set(report["resource_urls"]), registered)


if __name__ == "__main__":
    unittest.main()
