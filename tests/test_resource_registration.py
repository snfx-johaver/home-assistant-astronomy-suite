"""A Lovelace resource registrar must claim its own bundle and no other.

Run with: python -m unittest discover -s tests -p "test_*.py"

The defect this measures
------------------------
Every bundle is served out of one directory::

    /local/community/astronomy-cards/astronomy-cards.js?v=<version>
    /local/community/astronomy-cards/deepsky-cards.js?v=<version>

so a registrar that decides ownership with ``"astronomy-cards" in url`` matches
*both* -- the second one on its **directory** name. ``__init__.py`` did exactly
that, in the API path and again in the ``.storage`` fallback, while the deep-sky
registrar next to it compared against a string that happens to be unambiguous.

When the deep-sky resource is reached first, the astronomy registrar rewrites
**that** resource's URL to ``astronomy-cards.js`` and returns. The consequences
are worth stating precisely, because the obvious one is the mild one:

* the deep-sky resource is recreated by the next registrar in the same setup
  call, so the missing deep-sky cards are self-healing and a user never sees
  them go;
* the real astronomy resource was never visited, so it keeps its old ``?v=``
  **permanently** -- every later run finds the rewritten entry first, sees it
  already current, and returns. Browsers keep serving that dashboard the card
  bundle from whichever version it was stuck at;
* two resources now point at ``astronomy-cards.js``. That is a double
  evaluation of a bundle against one ``customElements`` registry, which is the
  state ``bundle-idempotency.test.mjs`` exists to make survivable.

What is asserted
----------------
One invariant, which is what the defect violates: **a registrar may change a
resource's cache-bust, never its filename.** Nothing here pairs a registrar
with "its" URL by name -- the pairing is the thing under test, so hard-coding
it would assume the answer.

Registrars and bundle URLs are both *discovered* from the module, so a third
bundle added later is covered without anyone extending this file. Resource
orderings are enumerated exhaustively rather than sampled, because the benign
order is the one a fresh install produces and the damaging order is the one
nobody tries.
"""

import asyncio
import itertools
import json
import re
import tempfile
import unittest
from pathlib import Path

from harness import load_component_module

package_init = load_component_module("__init__")

# ``?v=1.2.3`` -- the cache-bust a registrar is allowed to rewrite.
CACHE_BUST = re.compile(r"\?v=(?P<version>[^&]+)$")

# A version no release will ever be at, so every discovered URL starts stale
# and every registrar has work to do.
STALE = "0.0.1"


def bundle_urls():
    """Every module-level Lovelace resource URL, discovered not listed."""
    found = {}
    for name in dir(package_init):
        if name.startswith("__"):
            continue
        value = getattr(package_init, name)
        if isinstance(value, str) and CACHE_BUST.search(value):
            found[name] = value
    return found


def async_registrars():
    """Every ``_async_register_*_resource`` coroutine function on the module."""
    return {
        name: getattr(package_init, name)
        for name in dir(package_init)
        if name.startswith("_async_register")
        and name.endswith("_resource")
        and asyncio.iscoroutinefunction(getattr(package_init, name))
    }


def storage_registrars():
    """Every ``_register_*_via_storage`` function on the module."""
    return {
        name: getattr(package_init, name)
        for name in dir(package_init)
        if name.startswith("_register") and name.endswith("_via_storage")
    }


BUNDLE_URLS = bundle_urls()
ASYNC_REGISTRARS = async_registrars()
STORAGE_REGISTRARS = storage_registrars()


def filename_of(url):
    """The file a resource URL points at, ignoring the cache-bust."""
    return url.split("?", 1)[0].rsplit("/", 1)[-1]


def stale(url):
    return CACHE_BUST.sub(f"?v={STALE}", url)


class FakeResources:
    """Stands in for Home Assistant's Lovelace resource collection."""

    def __init__(self, urls):
        self.items = [
            {"id": f"id-{index}", "url": url, "type": "module"}
            for index, url in enumerate(urls)
        ]
        self.updated = []
        self.created = []

    def async_items(self):
        return list(self.items)

    async def async_update_item(self, item_id, updates):
        for item in self.items:
            if item["id"] == item_id:
                self.updated.append((item_id, item["url"], updates.get("url")))
                item.update({k: v for k, v in updates.items() if k == "url"})
                return
        raise KeyError(item_id)

    async def async_create_item(self, item):
        new = {"id": f"id-new-{len(self.created)}", **item}
        self.items.append(new)
        self.created.append(new["url"])
        return new

    def urls(self):
        return [item["url"] for item in self.items]


class FakeConfig:
    def __init__(self, root):
        self.root = Path(root)

    def path(self, *parts):
        return str(self.root.joinpath(*parts))


class FakeHass:
    """Just enough ``hass`` for the registration functions."""

    def __init__(self, root, resources=None):
        self.config = FakeConfig(root)
        self.data = {}
        if resources is not None:
            self.data["lovelace"] = {"resources": resources}

    async def async_add_executor_job(self, func, *args):
        return func(*args)


class DiscoveryTests(unittest.TestCase):
    """Non-vacuity: every loop below must have something to iterate."""

    def test_discovery_found_the_bundle_urls(self):
        self.assertGreaterEqual(len(BUNDLE_URLS), 2, BUNDLE_URLS)

    def test_discovery_found_the_registrars(self):
        self.assertGreaterEqual(len(ASYNC_REGISTRARS), 2, sorted(ASYNC_REGISTRARS))
        self.assertGreaterEqual(len(STORAGE_REGISTRARS), 2, sorted(STORAGE_REGISTRARS))

    def test_every_bundle_url_is_in_the_same_directory(self):
        """The premise of the defect, pinned so it cannot quietly stop holding.

        If the bundles ever move to separate directories this test file is
        measuring something that no longer exists, and it should say so
        loudly rather than keep passing for the wrong reason.
        """
        directories = {url.split("?", 1)[0].rsplit("/", 1)[0] for url in BUNDLE_URLS.values()}
        self.assertEqual(len(directories), 1, directories)

    def test_one_bundle_filename_contains_another_urls_directory(self):
        """Why a substring test on the whole URL cannot work here.

        This is a fact about the names that ship, not about the fix, so it
        passes before and after -- it is the reason the fix has to compare
        the filename rather than a substring.
        """
        directory = next(iter(BUNDLE_URLS.values())).split("?", 1)[0].rsplit("/", 1)[0]
        leaf = directory.rsplit("/", 1)[-1]
        confusable = [
            url for url in BUNDLE_URLS.values() if leaf in url and filename_of(url) != f"{leaf}.js"
        ]
        self.assertTrue(confusable, f"expected a URL under /{leaf}/ naming a different file")


class ApiPathTests(unittest.TestCase):
    """The ``hass.data['lovelace']`` registration path."""

    def _run_all(self, registrars, order):
        """Run ``registrars`` against resources listed in ``order``."""
        with tempfile.TemporaryDirectory() as scratch:
            resources = FakeResources([stale(url) for url in order])
            hass = FakeHass(scratch, resources)
            for registrar in registrars:
                asyncio.run(registrar(hass))
            return resources

    def _cases(self):
        """Every registrar order against every resource order.

        Both dimensions are enumerated rather than taken as given. The
        registrar order this module happens to iterate in is alphabetical,
        which coincides with the order ``async_setup_entry`` calls them --
        a coincidence, and one that would quietly stop holding the moment a
        bundle is added whose name sorts differently. A correct
        implementation does not depend on either order, so the test should
        not depend on getting them right.
        """
        for registrar_order in itertools.permutations(sorted(ASYNC_REGISTRARS)):
            registrars = [ASYNC_REGISTRARS[name] for name in registrar_order]
            for url_order in itertools.permutations(sorted(BUNDLE_URLS.values())):
                label = {
                    "registrars": [n.replace("_async_register_", "") for n in registrar_order],
                    "resources": [filename_of(u) for u in url_order],
                }
                yield registrars, url_order, label

    def test_no_registrar_changes_a_resources_filename(self):
        """The invariant. A cache-bust may be rewritten; a filename may not."""
        for registrars, order, label in self._cases():
            with self.subTest(**label):
                resources = self._run_all(registrars, order)
                renamed = [
                    (before, after)
                    for _, before, after in resources.updated
                    if after is not None and filename_of(before) != filename_of(after)
                ]
                self.assertEqual(
                    renamed,
                    [],
                    "a registrar rewrote a resource to point at a different bundle",
                )

    def test_every_bundle_ends_up_registered_exactly_once(self):
        """End state, which is what a user's resource list actually is."""
        expected = sorted(filename_of(url) for url in BUNDLE_URLS.values())
        for registrars, order, label in self._cases():
            with self.subTest(**label):
                resources = self._run_all(registrars, order)
                self.assertEqual(sorted(filename_of(u) for u in resources.urls()), expected)

    def test_every_resource_ends_up_at_the_current_version(self):
        """The stale-forever half: a resource nobody visits is never updated."""
        current = {filename_of(url): url for url in BUNDLE_URLS.values()}
        for registrars, order, label in self._cases():
            with self.subTest(**label):
                resources = self._run_all(registrars, order)
                stuck = [u for u in resources.urls() if u != current.get(filename_of(u))]
                self.assertEqual(stuck, [], f"still stale; expected {sorted(current.values())}")

    def test_a_registrar_updates_a_stale_resource_it_owns(self):
        """Non-vacuity: the tests above must not pass by doing nothing at all.

        Passes before and after the fix. Without it, a registrar that matched
        no resource ever would satisfy every invariant above trivially.
        """
        registrars = [ASYNC_REGISTRARS[name] for name in sorted(ASYNC_REGISTRARS)]
        resources = self._run_all(registrars, sorted(BUNDLE_URLS.values()))
        self.assertTrue(resources.updated, "no registrar updated anything")


class StoragePathTests(unittest.TestCase):
    """The ``.storage/lovelace_resources`` fallback, which had the same test.

    Reached through the async registrars with no ``hass.data['lovelace']``,
    rather than by calling the storage functions directly. That is how
    production reaches this code, and it means the order the fallbacks run in
    is the order the integration actually produces instead of whatever order
    this file happens to discover them in.
    """

    def _run_all(self, registrars, order):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        storage_dir = Path(scratch.name) / ".storage"
        storage_dir.mkdir(parents=True)
        path = storage_dir / "lovelace_resources"
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "key": "lovelace_resources",
                    "data": {
                        "items": [
                            {"url": stale(url), "type": "module", "id": f"id-{i}"}
                            for i, url in enumerate(order)
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        hass = FakeHass(scratch.name)  # no lovelace data -> storage fallback
        for registrar in registrars:
            asyncio.run(registrar(hass))
        return [i["url"] for i in json.loads(path.read_text(encoding="utf-8"))["data"]["items"]]

    def _cases(self):
        for registrar_order in itertools.permutations(sorted(ASYNC_REGISTRARS)):
            registrars = [ASYNC_REGISTRARS[name] for name in registrar_order]
            for url_order in itertools.permutations(sorted(BUNDLE_URLS.values())):
                label = {
                    "registrars": [n.replace("_async_register_", "") for n in registrar_order],
                    "resources": [filename_of(u) for u in url_order],
                }
                yield registrars, url_order, label

    def test_the_storage_fallback_is_the_path_under_test(self):
        """Non-vacuity: prove these tests are not silently using the API path.

        Passes before and after. If ``hass.data['lovelace']`` were present the
        assertions below would be re-testing ``ApiPathTests`` while claiming
        to cover the fallback -- the same file, twice, reported as two.
        """
        registrars = [ASYNC_REGISTRARS[name] for name in sorted(ASYNC_REGISTRARS)]
        urls = self._run_all(registrars, sorted(BUNDLE_URLS.values()))
        self.assertTrue(urls, "the storage file was never written")
        self.assertNotIn("lovelace", FakeHass("/tmp").data)

    def test_no_registrar_changes_a_resources_filename(self):
        before = sorted(filename_of(url) for url in BUNDLE_URLS.values())
        for registrars, order, label in self._cases():
            with self.subTest(**label):
                after = sorted(filename_of(u) for u in self._run_all(registrars, order))
                self.assertEqual(after, before)

    def test_every_resource_ends_up_at_the_current_version(self):
        current = {filename_of(url): url for url in BUNDLE_URLS.values()}
        for registrars, order, label in self._cases():
            with self.subTest(**label):
                stuck = [
                    u for u in self._run_all(registrars, order) if u != current.get(filename_of(u))
                ]
                self.assertEqual(stuck, [])

    def test_an_unrelated_resource_is_left_alone(self):
        """Non-vacuity and scope: the registrars must not touch other cards.

        Passes before and after -- ``mini-graph-card`` contains neither
        marker, so no version of the matching logic claims it.
        """
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        storage_dir = Path(scratch.name) / ".storage"
        storage_dir.mkdir(parents=True)
        path = storage_dir / "lovelace_resources"
        foreign = "/local/community/mini-graph-card/mini-graph-card-bundle.js?v=0.11.0"
        path.write_text(
            json.dumps({"data": {"items": [{"url": foreign, "type": "module", "id": "x"}]}}),
            encoding="utf-8",
        )
        hass = FakeHass(scratch.name)
        for name in sorted(ASYNC_REGISTRARS):
            asyncio.run(ASYNC_REGISTRARS[name](hass))
        urls = [i["url"] for i in json.loads(path.read_text(encoding="utf-8"))["data"]["items"]]
        self.assertIn(foreign, urls)


if __name__ == "__main__":
    unittest.main()
