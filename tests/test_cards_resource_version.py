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
import re
import unittest
from pathlib import Path

from harness import COMPONENT_DIR, load_component_module

package_init = load_component_module("__init__")

MANIFEST_PATH = COMPONENT_DIR / "manifest.json"

# Matches the ``?v=1.2.3`` cache-bust these URLs are built with.
CACHE_BUST = re.compile(r"\?v=(?P<version>[^&]+)$")


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
        import os
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = COMPONENT_DIR.parent.parent
        # The script prints "→" in its progress output, which explodes on a
        # cp1252 console. Force UTF-8 so this tests the script's logic rather
        # than the terminal it happens to be running under.
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / "repo"
            shutil.copytree(
                repo,
                copy,
                ignore=shutil.ignore_patterns(".git", "node_modules", "*.png"),
            )
            result = subprocess.run(
                [sys.executable, str(copy / "scripts" / "bump_version.py"), "patch", "--no-git"],
                cwd=copy,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )
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
                env=env,
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


if __name__ == "__main__":
    unittest.main()
