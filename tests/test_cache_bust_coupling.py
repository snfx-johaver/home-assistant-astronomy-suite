"""A card bundle's cache-bust must move when the bundle's bytes move.

Run with: python -m unittest discover -s tests -p "test_*.py"

The defect this measures
-----------------------
``test_cards_resource_version.py`` already states the failure mode exactly:

    if it stops tracking the release, the URL stops changing, the comparison
    finds them equal, the resource is left alone, and browsers keep serving
    the previous card bundle from cache.

That is right, and it guards one of the two ways to get there. The URL was
built from ``manifest.json``; the deployed bytes are written by
``shutil.copy2`` from the component directory. **Nothing couples them.** So
the other way in is to change the bundle without cutting a release -- a
hand-copied file, a local rebuild, a partially-applied update -- and the key
sits still while the bytes move underneath it.

It is not a cosmetic key. Home Assistant serves ``/local/`` with
``Cache-Control: public, max-age=2678400`` and no revalidation, so for 31 days
the URL is the *only* thing that can dislodge a cached bundle: the ETag is
never consulted. A browser that loaded the dashboard before the swap keeps
running the old cards for a month, the integration reports itself updated, and
no log line anywhere is wrong.

This was measured on a live install, not imagined: ``manifest.json`` at one
version, the bundle banner at a later one, the deployed file's mtime 21 hours
after the release it claimed to be, and the resource URL still carrying the
older key.

What is asserted
----------------
The invariant is about *bytes*, not about text: change a bundle, and the URL
that serves it must change. Nothing here names the function that computes the
key or the shape of the value, so a different derivation that also couples the
two -- a longer digest, an mtime, a build id -- passes unchanged. The test is
run by mutating a real bundle in a throwaway copy of the package and importing
it, which is what Home Assistant does.

The converse is asserted too: touching one bundle must leave the *other*
bundle's URL alone. A key derived from something too coarse -- the directory,
a release timestamp -- would satisfy the first assertion and fail this one,
and would silently expire every cached bundle on every deploy.

Bundles are discovered from the package rather than listed, so a third one is
covered without anyone extending this file.
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

from harness import COMPONENT_DIR

HARNESS_PATH = Path(__file__).resolve().parent / "harness.py"
MANIFEST_PATH = COMPONENT_DIR / "manifest.json"

CACHE_BUST = re.compile(r"\?v=(?P<key>[^&]+)$")

# The script and probes print non-ASCII; force UTF-8 so these tests measure
# behaviour rather than the console they happen to run under.
CHILD_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

# Imports the package the way Home Assistant would and reports every
# module-level string carrying a cache-bust. Deliberately reads the *URLs*
# rather than any helper: the helper is an implementation detail, the URL is
# what a browser is asked to fetch.
PROBE = (
    "import sys, json;"
    "sys.path.insert(0, sys.argv[1]);"
    "from harness import load_component_module;"
    "m = load_component_module('__init__');"
    "print(json.dumps({n: getattr(m, n) for n in dir(m)"
    " if not n.startswith('__') and isinstance(getattr(m, n), str)"
    " and '?v=' in getattr(m, n)}))"
)


def bundle_names():
    """Every card bundle that ships inside the component package."""
    return sorted(p.name for p in COMPONENT_DIR.glob("*-cards.js"))


BUNDLE_NAMES = bundle_names()


def manifest_version():
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["version"]


def importable_copy(scratch):
    """A throwaway copy of just what is needed to import the package.

    The whole repository is not needed and copying it is slow; the images in
    particular are half a megabyte and cannot affect a card bundle's URL.
    """
    root = Path(scratch) / "repo"
    (root / "tests").mkdir(parents=True)
    shutil.copytree(
        COMPONENT_DIR,
        root / "custom_components" / "nasa_astronomy",
        ignore=shutil.ignore_patterns("__pycache__", "*.png"),
    )
    shutil.copy2(HARNESS_PATH, root / "tests" / "harness.py")
    return root


def urls_from(root):
    """Import the copied package in a fresh interpreter and read its URLs.

    A subprocess rather than a reload: the module caches in ``sys.modules``,
    and a stale entry would make a changed bundle look unchanged, which is the
    exact conclusion this file exists to be able to trust.
    """
    result = subprocess.run(
        [sys.executable, "-c", PROBE, str(root / "tests")],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=CHILD_ENV,
    )
    if result.returncode != 0:
        raise AssertionError(f"probe failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def url_for(urls, filename):
    for url in urls.values():
        if url.split("?", 1)[0].rsplit("/", 1)[-1] == filename:
            return url
    raise AssertionError(f"no URL serves {filename}: {sorted(urls.values())}")


class DiscoveryTests(unittest.TestCase):
    """Non-vacuity: every loop below must have something to iterate."""

    def test_discovery_found_the_bundles(self):
        self.assertGreaterEqual(len(BUNDLE_NAMES), 2, BUNDLE_NAMES)

    def test_every_shipped_bundle_has_a_versioned_url(self):
        """A bundle with no URL is a bundle nothing can cache-bust.

        Passes before and after. It is the enumeration guard: the failure
        being defended against is a third bundle added later whose URL nobody
        remembered to build, and a hand-written list here would share exactly
        that blind spot.
        """
        with tempfile.TemporaryDirectory() as scratch:
            urls = urls_from(importable_copy(scratch))
        served = sorted(u.split("?", 1)[0].rsplit("/", 1)[-1] for u in urls.values())
        self.assertEqual(served, BUNDLE_NAMES)


class CacheBustCouplingTests(unittest.TestCase):
    """The invariant: the key is a function of the bytes it serves."""

    def test_changing_a_bundles_bytes_changes_that_bundles_url(self):
        """The whole defect, in one assertion.

        Appending a comment is a real edit -- it is what a rebuild or a
        hand-patch looks like -- and it leaves ``manifest.json`` untouched,
        which is the condition under which the old key stood still.
        """
        for name in BUNDLE_NAMES:
            with self.subTest(bundle=name), tempfile.TemporaryDirectory() as scratch:
                root = importable_copy(scratch)
                before = urls_from(root)

                target = root / "custom_components" / "nasa_astronomy" / name
                target.write_bytes(target.read_bytes() + b"\n// edited\n")

                after = urls_from(root)
                self.assertNotEqual(
                    url_for(after, name),
                    url_for(before, name),
                    f"{name} changed but the URL serving it did not, so every "
                    "browser holding the old bundle keeps it until the "
                    "cache entry expires",
                )

    def test_changing_one_bundle_leaves_the_others_url_alone(self):
        """Precision. A key too coarse would expire every bundle on every deploy.

        This is the assertion a directory digest, a build timestamp or a
        release id would fail while still passing the test above.
        """
        if len(BUNDLE_NAMES) < 2:
            self.skipTest("needs two bundles to tell coupling from coarseness")
        for name in BUNDLE_NAMES:
            others = [n for n in BUNDLE_NAMES if n != name]
            with self.subTest(edited=name), tempfile.TemporaryDirectory() as scratch:
                root = importable_copy(scratch)
                before = urls_from(root)

                target = root / "custom_components" / "nasa_astronomy" / name
                target.write_bytes(target.read_bytes() + b"\n// edited\n")

                after = urls_from(root)
                for other in others:
                    self.assertEqual(
                        url_for(after, other),
                        url_for(before, other),
                        f"editing {name} moved {other}'s cache-bust too",
                    )

    def test_a_line_ending_only_change_still_moves_the_url(self):
        """The digest must be of the bytes served, not of their meaning.

        Every other test here mutates *content*, so all of them stay green
        under a digest that normalises before hashing -- ``read_text()``
        instead of ``read_bytes()``, or an explicit ``\\r\\n`` -> ``\\n``
        pass. This one does not, and it is the only thing standing between
        the fix and that refactor.

        The refactor is plausible rather than hypothetical, because there is
        a real observation that invites it: this repository has no
        ``.gitattributes``, so a checkout with ``core.autocrlf=true`` renders
        the bundle with CRLF while CI renders it with LF. The same release
        therefore has two byte-identities and two keys. That looks like an
        inconsistency worth normalising away, and normalising it away is
        precisely wrong -- those two renderings *are* two different responses
        to the same URL, differing by ~3 kB, and a browser holding one of
        them has no way to learn about the other.

        The key's job is not to identify a release. It is to change whenever
        what gets sent over the wire changes.
        """
        for name in BUNDLE_NAMES:
            with self.subTest(bundle=name), tempfile.TemporaryDirectory() as scratch:
                root = importable_copy(scratch)
                before = urls_from(root)

                target = root / "custom_components" / "nasa_astronomy" / name
                original = target.read_bytes()
                # Flip to whichever ending the file is not currently using.
                # Hard-coding a direction would make this a no-op on half the
                # platforms it runs on -- green, and measuring nothing.
                as_lf = original.replace(b"\r\n", b"\n")
                reflowed = as_lf if as_lf != original else as_lf.replace(b"\n", b"\r\n")
                self.assertNotEqual(
                    reflowed,
                    original,
                    f"{name} has no newlines to reflow, so this test would "
                    "assert nothing -- it must be rewritten, not skipped",
                )
                target.write_bytes(reflowed)

                after = urls_from(root)
                self.assertNotEqual(
                    url_for(after, name),
                    url_for(before, name),
                    f"{name} is now {len(reflowed) - len(original)} bytes "
                    "different on the wire but its URL did not move, so the "
                    "key is measuring the file's meaning rather than its bytes",
                )

    def test_identical_bytes_produce_an_identical_url(self):
        """Non-vacuity, and the property that makes the key usable.

        Passes before and after the fix. Without it, a key that simply changed
        on every import -- a random value, a timestamp -- would satisfy the
        coupling test above while busting every cache on every restart.
        """
        with tempfile.TemporaryDirectory() as scratch:
            root = importable_copy(scratch)
            self.assertEqual(urls_from(root), urls_from(root))

    def test_every_url_still_carries_the_release_version(self):
        """The half the release apparatus already guards, kept.

        Passes before and after. The version is what a human reads in the
        Lovelace resource list, and eighteen releases of machinery exist to
        keep it truthful; coupling the key to the bytes must not cost that.
        """
        expected = manifest_version()
        with tempfile.TemporaryDirectory() as scratch:
            urls = urls_from(importable_copy(scratch))
        for name, url in sorted(urls.items()):
            with self.subTest(url=name):
                key = CACHE_BUST.search(url)
                self.assertIsNotNone(key, url)
                self.assertTrue(
                    key.group("key").startswith(expected),
                    f"{url} does not name the release {expected!r}",
                )


if __name__ == "__main__":
    unittest.main()
