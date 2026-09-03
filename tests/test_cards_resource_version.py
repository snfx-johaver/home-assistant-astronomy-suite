"""The Lovelace card cache-bust must carry the released version.

Run with: python -m unittest discover -s tests -p "test_*.py"

``__init__.py`` builds its Lovelace resource URLs with a version query string::

    CARDS_LOCAL_URL = f"/local/community/astronomy-cards/astronomy-cards.js?v={VERSION}"

and ``_async_register_cards_resource`` decides whether to rewrite a registered
resource by comparing ``resource["url"] != CARDS_LOCAL_URL``. So ``VERSION`` is
not cosmetic: if it stops tracking the release, the URL stops changing, the
comparison finds them equal, the resource is left alone, and browsers keep
serving the previous card bundle from cache. The integration reports itself as
updated while the dashboard is running old code, with nothing in the log.

Why this file exists even though the value is currently correct
--------------------------------------------------------------
This is a guard against a latent defect, not a fix for a live one --
``scripts/bump_version.py`` was rewriting the literal on every release, so it
was in step. There is therefore no honest "must fail before the fix" run to
report: the assertion below passed against the literal too. Its control is the
perturbation instead, which is the right control for a test whose job is to
notice future drift rather than to prove a present bug.

What changed is that the version is now derived from ``manifest.json`` rather
than rewritten by the release script, so the class of failure this guards
against -- a release that does not go through ``bump_version.py``, or a
refactor that stops the script's regex matching -- can no longer happen
silently.

The versioned URLs are *discovered* from the module namespace rather than
listed, so a third card bundle added later is covered without anyone
remembering to extend this file.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import COMPONENT_DIR, load_component_module

package_init = load_component_module("__init__")

REPO_ROOT = COMPONENT_DIR.parent.parent
MANIFEST_PATH = COMPONENT_DIR / "manifest.json"

# The script prints "→" in its progress output, which explodes on a cp1252
# console. Force UTF-8 so these tests measure the script's logic rather than
# the terminal it happens to be running under.
CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

# Matches the ``?v=1.2.3`` cache-bust these URLs are built with.
CACHE_BUST = re.compile(r"\?v=(?P<version>[^&]+)$")

# The version constant inside a card bundle. Bundles name it differently
# (``VERSION``, ``DEEPSKY_VERSION``), so match the suffix rather than listing.
BUNDLE_VERSION = re.compile(r'const [A-Z_]*VERSION = "(?P<version>[^"]+)"')

# The two directories a card bundle ships from. They must stay byte-identical
# (see README "Architecture").
CARD_DIRS = (
    Path("custom_components") / "nasa_astronomy",
    Path("www") / "community" / "astronomy-cards",
)


def discover_bundles():
    """Map each card bundle filename to its copies, discovered not listed.

    Enumerating from disk is the point: the failure this guards against is a
    bundle nobody remembered to register with the release script, so a
    hand-written list here would share the blind spot it is meant to catch.
    """
    names = sorted(
        {p.name for d in CARD_DIRS for p in (REPO_ROOT / d).glob("*-cards.js")}
    )
    return {name: tuple(d / name for d in CARD_DIRS) for name in names}


BUNDLE_COPIES = discover_bundles()

# Every file a release rewrites, relative to the repo root.
VERSIONED_FILES = (
    Path("version.json"),
    Path("custom_components") / "nasa_astronomy" / "manifest.json",
    Path("www") / "community" / "astronomy-cards" / "package.json",
) + tuple(copy for copies in BUNDLE_COPIES.values() for copy in copies)


def manifest_version():
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)["version"]


def versioned_urls():
    """Every module-level string constant carrying a ``?v=`` cache-bust."""
    found = {}
    for name in dir(package_init):
        if name.startswith("__"):
            continue
        value = getattr(package_init, name)
        if isinstance(value, str):
            match = CACHE_BUST.search(value)
            if match:
                found[name] = match.group("version")
    return found


VERSIONED_URLS = versioned_urls()


class CardResourceVersionTests(unittest.TestCase):
    """The cache-bust must be the released version, or dashboards serve stale code."""

    def test_discovery_found_the_versioned_urls(self):
        """Non-vacuity: the assertions below must not pass over an empty dict.

        Two bundles ship today -- ``astronomy-cards.js`` and
        ``deepsky-cards.js`` -- so anything less means discovery broke.
        """
        self.assertGreaterEqual(len(VERSIONED_URLS), 2, VERSIONED_URLS)

    def test_module_version_is_the_manifest_version(self):
        self.assertEqual(package_init.VERSION, manifest_version())

    def test_every_versioned_url_carries_the_manifest_version(self):
        expected = manifest_version()
        wrong = {
            name: version
            for name, version in VERSIONED_URLS.items()
            if version != expected
        }
        self.assertEqual(wrong, {}, f"manifest.json says {expected!r}")


# Both card bundles, in the order bump_version.py processes them.
BUNDLES = BUNDLE_COPIES["astronomy-cards.js"]


def copy_of_the_repo(scratch):
    copy = Path(scratch) / "repo"
    shutil.copytree(
        REPO_ROOT,
        copy,
        ignore=shutil.ignore_patterns(".git", "node_modules", "*.png"),
    )
    return copy


def run_bumper(copy):
    return subprocess.run(
        [sys.executable, str(copy / "scripts" / "bump_version.py"), "patch", "--no-git"],
        cwd=copy,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=CHILD_ENV,
    )


def rename_the_product_in(bundle_path):
    """Break the header pattern the way a real product rename would."""
    bundle_path.write_text(
        bundle_path.read_text(encoding="utf-8").replace(
            "Astronomy Space Suite Cards v", "Stellar Suite Cards v"
        ),
        encoding="utf-8",
    )


def break_the_version_constant_in(bundle_path):
    """Rename a bundle's version identifier so the release pattern misses it."""
    bundle_path.write_text(
        BUNDLE_VERSION.sub(
            lambda m: m.group(0).replace("VERSION", "VERSION_RENAMED", 1),
            bundle_path.read_text(encoding="utf-8"),
            count=1,
        ),
        encoding="utf-8",
    )


class CardBundleVersionTests(unittest.TestCase):
    """Every shipped card bundle must report the released version.

    ``deepsky-cards.js`` sat at ``1.0.0`` while the suite reached ``1.11.4``.
    It was never independently versioned -- ``git log -S`` shows the constant
    changed exactly once, in the commit that created it, across six later
    modifications including a feature addition and a five-defect fix. An
    artefact with a real independent version bumps when it changes.

    It is user-visible: the bundle logs ``v${DEEPSKY_VERSION}`` to the console
    on load, so anyone debugging a deep-sky card read a confident wrong number.
    That is the same defect as one device advertising four ``sw_version``
    values, in a different costume.
    """

    def test_discovery_found_both_bundles(self):
        """Non-vacuity: the per-bundle assertions must not loop over nothing."""
        self.assertEqual(
            sorted(BUNDLE_COPIES), ["astronomy-cards.js", "deepsky-cards.js"]
        )

    def test_every_card_bundle_reports_the_manifest_version(self):
        expected = manifest_version()
        for name, copies in BUNDLE_COPIES.items():
            for copy in copies:
                with self.subTest(bundle=str(copy)):
                    found = BUNDLE_VERSION.search(
                        (REPO_ROOT / copy).read_text(encoding="utf-8")
                    )
                    self.assertIsNotNone(found, f"{name} has no version constant")
                    self.assertEqual(found.group("version"), expected)


class ReleaseScriptTests(unittest.TestCase):
    """The release path must survive the constant becoming derived.

    ``bump_version.py`` used to rewrite ``VERSION = "x.y.z"`` here and
    ``raise SystemExit`` when its regex found nothing, so leaving that step in
    place would abort every future release. Rather than grep the script for the
    removed function -- which would measure its text, not its behaviour -- this
    runs the real thing against a throwaway copy of the tree and checks the
    versions it writes actually agree afterwards.
    """

    def test_a_release_bump_keeps_every_version_in_step(self):
        with tempfile.TemporaryDirectory() as scratch:
            copy = copy_of_the_repo(scratch)
            result = run_bumper(copy)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            manifest = json.loads(
                (copy / "custom_components" / "nasa_astronomy" / "manifest.json").read_text()
            )
            release = json.loads((copy / "version.json").read_text())
            self.assertEqual(manifest["version"], release["integration"])
            self.assertNotEqual(manifest["version"], manifest_version())  # it really bumped

            # The derived constant must actually follow the bump with nothing
            # rewriting it. Asserting on the copy's *source text* would measure
            # the characters again; instead load the bumped copy and read what
            # it resolves to, which is what Home Assistant would see.
            probe = (
                "import sys, json;"
                "sys.path.insert(0, sys.argv[1]);"
                "from harness import load_component_module;"
                "m = load_component_module('__init__');"
                "print(json.dumps({'version': m.VERSION,"
                " 'cards': m.CARDS_LOCAL_URL,"
                " 'deepsky': m.DEEPSKY_CARDS_LOCAL_URL}))"
            )
            probed = subprocess.run(
                [sys.executable, "-c", probe, str(copy / "tests")],
                cwd=copy,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=CHILD_ENV,
            )
            self.assertEqual(probed.returncode, 0, probed.stdout + probed.stderr)
            resolved = json.loads(probed.stdout.strip().splitlines()[-1])

            bumped = manifest["version"]
            self.assertEqual(resolved["version"], bumped)
            for key in ("cards", "deepsky"):
                self.assertEqual(
                    CACHE_BUST.search(resolved[key]).group("version"),
                    bumped,
                    resolved[key],
                )


class AbortedReleaseTests(unittest.TestCase):
    """A release that cannot complete must not half-happen.

    ``bump_version.py`` validates each substitution and raises ``SystemExit``
    when a pattern stops matching. That guard is right -- it exists because the
    bundle was once renamed and the banner drifted silently -- but it fires
    *after* earlier files have already been written, so a failed release leaves
    ``version.json``, ``manifest.json``, ``package.json`` and the first card
    bundle bumped while the second still carries the old version.

    That is worse than it sounds, because the two bundles are required to stay
    byte-identical (see README "Architecture"). The guard protects an invariant
    from a position where tripping it violates that invariant.

    The perturbation below breaks the *product-name* pattern rather than the
    ``const VERSION`` one deliberately. ``Astronomy Space Suite Cards v`` is
    marketing text, and it is the pattern that broke last time: whoever renames
    the product next will correctly believe they are not touching code.

    It is broken in the **second** bundle only, so the first is already written
    by the time the script gives up -- which is precisely the state this test
    exists to forbid.
    """

    BUNDLES = BUNDLES
    VERSIONED_FILES = VERSIONED_FILES

    def test_an_aborted_bump_leaves_every_file_unmodified(self):
        with tempfile.TemporaryDirectory() as scratch:
            copy = copy_of_the_repo(scratch)

            # Rename the product in the second bundle so its header pattern
            # stops matching, exactly as a real rename would.
            rename_the_product_in(copy / self.BUNDLES[1])

            before = {
                str(rel): (copy / rel).read_bytes() for rel in self.VERSIONED_FILES
            }

            result = run_bumper(copy)

            # Non-vacuity: these hold both before and after the fix. The point
            # is not that the script stops -- it already does -- but what it
            # leaves behind when it does.
            self.assertNotEqual(result.returncode, 0, "the bump should have aborted")
            self.assertIn("header/banner", result.stdout + result.stderr)

            changed = sorted(
                name for name, original in before.items()
                if (copy / name).read_bytes() != original
            )
            self.assertEqual(
                changed,
                [],
                "an aborted release left a half-bumped tree; these were written "
                f"before the script gave up: {changed}",
            )

    def test_an_aborted_bump_does_not_diverge_the_two_bundles(self):
        """The invariant the guard is supposed to protect.

        Stated in version terms rather than byte terms, because the
        perturbation above necessarily makes the two files differ textually.
        """
        with tempfile.TemporaryDirectory() as scratch:
            copy = copy_of_the_repo(scratch)
            rename_the_product_in(copy / self.BUNDLES[1])

            result = run_bumper(copy)
            self.assertNotEqual(result.returncode, 0, "the bump should have aborted")

            versions = {
                str(rel): BUNDLE_VERSION.search(
                    (copy / rel).read_text(encoding="utf-8")
                ).group("version")
                for rel in self.BUNDLES
            }
            self.assertEqual(
                len(set(versions.values())),
                1,
                f"the two card bundles must never disagree on version: {versions}",
            )

    def test_every_card_bundle_is_covered_by_the_release_script(self):
        """A bundle the script does not know about is a bundle that will drift.

        Coverage is measured, not declared: for each bundle discovered on disk,
        break its version constant and require the release to notice. Reading
        the script's own list of registered bundles would only confirm the list
        agrees with itself -- and ``deepsky-cards.js`` shipped for fourteen
        releases precisely because it was absent from that list.

        The break is applied to the *second* copy so that, under a script that
        writes as it goes, the first is already committed when it gives up.
        """
        for name, copies in BUNDLE_COPIES.items():
            with self.subTest(bundle=name), tempfile.TemporaryDirectory() as scratch:
                copy = copy_of_the_repo(scratch)
                break_the_version_constant_in(copy / copies[1])

                before = {
                    str(rel): (copy / rel).read_bytes() for rel in VERSIONED_FILES
                }
                result = run_bumper(copy)

                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"{name} is not covered by the release script: renaming its "
                    "version constant changed nothing and the bump still "
                    f"succeeded.\n{result.stdout}",
                )
                changed = sorted(
                    rel for rel, original in before.items()
                    if (copy / rel).read_bytes() != original
                )
                self.assertEqual(
                    changed, [], f"aborting on {name} left a half-bumped tree: {changed}"
                )


if __name__ == "__main__":
    unittest.main()
