"""The cache-bust key must describe the bytes the browser is served.

Run with: python -m unittest discover -s tests -p "test_*.py"

The defect this measures
------------------------
``?v=`` keys were derived from the bundle inside the integration directory::

    CARDS_LOCAL_URL = (
        f"/local/community/astronomy-cards/{CARDS_FILENAME}"
        f"?v={_cache_bust_for(Path(__file__).parent / CARDS_FILENAME)}"
    )

but ``/local/`` is ``config/www``, and ``_deploy_cards_to_www`` *copies* the
bundle there. So the digest measured the **input** of ``shutil.copy2`` while
the URL addressed its **output**. Two files, one claim.

On a healthy install the two copies agree, which is exactly why this survived
review: every observable is consistent. They come apart in the case the key
exists to handle -- when the deploy does not run, or runs and skips a file --
and then the key moves while the served bytes stand still. Home Assistant
serves ``/local/`` with ``max-age=2678400`` and no revalidation, so that
advertises a fresh URL for a stale bundle and pins it for 31 days. A
cache-bust that does that is worse than none.

How it is measured
------------------
Behaviourally, and through an interface that exists on **both** sides of the
fix: the URL a registrar actually writes into
``.storage/lovelace_resources``. That is the literal string a browser is
handed, and it is what the live install was read from.

Nothing here asserts a key *format*. The property is an invariance -- the key
is a function of the served bytes and of nothing else -- so it is measured by
changing one input at a time and watching the key follow or stand still. A
test that recomputed ``f"{VERSION}-{sha256[:12]}"`` would restate the
implementation and pass for any two implementations that agree, including two
that are both wrong.

The bundles are discovered from ``DEPLOYED_FILENAMES`` rather than listed, so
a third bundle added later is covered without editing this file -- the failure
being guarded against is precisely the one nobody remembered to add.
"""
import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import MinimalHass, load_component_module

package_init = load_component_module("__init__")


def bundles():
    """Every deployed file a browser imports as a module, discovered."""
    return [name for name in package_init.DEPLOYED_FILENAMES if name.endswith(".js")]


BUNDLES = bundles()


def async_registrars():
    """Every ``_async_register_*_resource`` coroutine on the module."""
    return [
        getattr(package_init, name)
        for name in sorted(dir(package_init))
        if name.startswith("_async_register")
        and name.endswith("_resource")
        and asyncio.iscoroutinefunction(getattr(package_init, name))
    ]


def filename_of(url):
    return url.split("?", 1)[0].rsplit("/", 1)[-1]


def key_of(url):
    return url.split("?v=", 1)[1]


def register(hass):
    """Run every registrar and return the keys it wrote, keyed by filename.

    ``hass.data`` has no ``lovelace`` entry, so every registrar falls through
    to the ``.storage`` path. That is not a convenience: reading the live
    install showed two resources carrying literal ids that
    ``async_create_item`` cannot generate, so the ``.storage`` fallback is the
    branch that actually ran there.

    Registrars run twice because the deep-sky one returns early when the
    storage file does not yet exist. One pass would make the result depend on
    the order they happen to be discovered in, which is a property of this
    file rather than of the integration.
    """
    for _ in range(2):
        for registrar in async_registrars():
            asyncio.run(registrar(hass))

    storage = Path(hass.config.path(".storage")) / "lovelace_resources"
    items = json.loads(storage.read_text())["data"]["items"]
    return {filename_of(i["url"]): key_of(i["url"]) for i in items}


class DiscoveryTests(unittest.TestCase):
    """Non-vacuity: every loop below must have something to iterate."""

    def test_discovery_found_the_bundles(self):
        self.assertGreaterEqual(len(BUNDLES), 2, BUNDLES)

    def test_discovery_found_the_registrars(self):
        self.assertGreaterEqual(len(async_registrars()), 2)


class ServedBytesTests(unittest.TestCase):
    """The key is a function of the served copy, and of nothing else."""

    def _install(self, stack):
        """A deployed install, as ``async_setup_entry`` leaves one."""
        root = stack.enter_context(tempfile.TemporaryDirectory())
        hass = MinimalHass(root)
        package_init._deploy_cards_to_www(hass)
        return hass

    def setUp(self):
        import contextlib

        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)

    def served(self, hass, name):
        return package_init.deployed_dir(hass) / name

    def test_changing_the_served_bytes_changes_the_registered_key(self):
        """The whole defect, in one assertion.

        Overwriting the file under ``www/`` and leaving the integration
        directory alone is not a contrived state -- it is what a hand-copied
        bundle looks like, and it is what was found on the one live install:
        two bundles written there at 23:28 and 23:33 over an install HACS had
        delivered at 14:55.

        A key taken from the integration directory cannot see that edit, so it
        keeps advertising the URL the browser already has cached.
        """
        hass = self._install(self.stack)
        before = register(hass)

        for name in BUNDLES:
            path = self.served(hass, name)
            path.write_bytes(path.read_bytes() + b"\n// hand-copied\n")

        after = register(hass)

        for name in BUNDLES:
            with self.subTest(name):
                self.assertNotEqual(
                    after[name],
                    before[name],
                    f"{name}: the served bytes changed and the key did not",
                )

    def test_the_key_ignores_bytes_no_browser_receives(self):
        """Precision, and the other half of the invariance.

        A key that changed on *any* edit anywhere would pass the test above
        while busting every cache on every unrelated touch. Restoring the
        served bytes must restore the key exactly, which pins the key to one
        input rather than merely making it sensitive.
        """
        hass = self._install(self.stack)
        original = {name: self.served(hass, name).read_bytes() for name in BUNDLES}
        before = register(hass)

        for name in BUNDLES:
            self.served(hass, name).write_bytes(original[name] + b"\n// churn\n")
        register(hass)

        for name in BUNDLES:
            self.served(hass, name).write_bytes(original[name])
        restored = register(hass)

        self.assertEqual(restored, before)

    def test_a_key_is_stable_while_nothing_moves(self):
        """Non-vacuity. Passes before and after the fix.

        Without it, an implementation that returned a random value on every
        call would satisfy the coupling test above while making every restart
        re-download every bundle.
        """
        hass = self._install(self.stack)
        self.assertEqual(register(hass), register(hass))

    def test_every_registered_key_names_the_release(self):
        """Non-vacuity. Passes before and after the fix.

        The version is what a human reads in the Lovelace resource list, and
        the release apparatus exists to keep it truthful. Coupling the key to
        the served bytes must not cost that.
        """
        hass = self._install(self.stack)
        keys = register(hass)
        self.assertGreaterEqual(len(keys), len(BUNDLES))
        for name, key in keys.items():
            with self.subTest(name):
                self.assertTrue(
                    key == package_init.VERSION
                    or key.startswith(f"{package_init.VERSION}-"),
                    f"{name}: {key} does not name {package_init.VERSION}",
                )


class DegradedKeyTests(unittest.TestCase):
    """A key that cannot be computed must say so."""

    def test_an_unreadable_bundle_yields_a_visibly_degraded_key(self):
        """``_cache_bust_for`` must not impersonate the format it replaced.

        Returning the bare version is not a neutral fallback: it is character
        for character the key this integration emitted before any digest
        existed, and it is what the live install is serving today. A degraded
        key in that format cannot be told apart from unfixed code -- not in a
        resource list, not in a diagnostics report, not in a network tab.

        The failure is silent by construction, which is the only reason it is
        worth a test: everything downstream keeps working and keeps agreeing.
        """
        with tempfile.TemporaryDirectory() as tmp:
            degraded = package_init._cache_bust_for(Path(tmp) / "absent.js")

        self.assertTrue(
            degraded.startswith(package_init.VERSION),
            f"{degraded} does not name the release",
        )
        self.assertNotEqual(
            degraded,
            package_init.VERSION,
            "a degraded key is indistinguishable from the pre-digest format",
        )


if __name__ == "__main__":
    unittest.main()
