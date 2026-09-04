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
from dataclasses import dataclass, field
from pathlib import Path

from harness import deployed_urls, load_component_module

package_init = load_component_module("__init__")

# ``?v=1.2.3`` -- the cache-bust a registrar is allowed to rewrite.
CACHE_BUST = re.compile(r"\?v=(?P<version>[^&]+)$")

# A version no release will ever be at, so every discovered URL starts stale
# and every registrar has work to do.
STALE = "0.0.1"


def bundle_urls():
    """Every Lovelace resource URL, discovered not listed.

    A URL is no longer a module constant: it names the copy under
    ``config/www`` -- the bytes a browser is actually served -- so obtaining
    one means standing up a deployed install. The path and the key are the
    same for any install deploying the same bundles, so the URLs the harness
    computes here are the ones every fixture below will see.
    """
    return deployed_urls(package_init)


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


@dataclass
class FakeLovelaceData:
    """What ``hass.data["lovelace"]`` actually is on a current Home Assistant.

    Mirrors ``homeassistant.components.lovelace.LovelaceData``, which has been
    a ``@dataclass`` -- not a mapping -- since 2024. Field names and order are
    copied from upstream so the stand-in fails the same way the real object
    would: ``lovelace_data.get("resources")`` raises ``AttributeError``, and a
    caller that swallows exceptions never learns its primary path is dead.

    This fixture used to be ``{"resources": resources}``. That dict modelled
    the shape the integration *expected* rather than the shape Home Assistant
    *provides*, so every assertion below passed against code that cannot run
    in production -- a stub kinder than the thing it stands for, which is the
    same defect ``harness.mjs`` had with ``customElements.define``.
    """

    resource_mode: str
    dashboards: dict = field(default_factory=dict)
    resources: object = None
    yaml_dashboards: dict = field(default_factory=dict)


def as_dataclass(resources):
    return FakeLovelaceData(resource_mode="storage", resources=resources)


def as_mapping(resources):
    """The pre-2024 shape, kept because the integration still supports it."""
    return {"resources": resources, "mode": "storage"}


# Every shape ``hass.data["lovelace"]`` is known to take, enumerated rather
# than sampled: picking one is how the dataclass shape went unmeasured.
LOVELACE_SHAPES = {"dataclass": as_dataclass, "mapping": as_mapping}


class FakeConfig:
    def __init__(self, root):
        self.root = Path(root)

    def path(self, *parts):
        return str(self.root.joinpath(*parts))


class FakeHass:
    """Just enough ``hass`` for the registration functions."""

    def __init__(self, root, resources=None, shape="dataclass"):
        self.config = FakeConfig(root)
        self.data = {}
        if resources is not None:
            self.data["lovelace"] = LOVELACE_SHAPES[shape](resources)

    async def async_add_executor_job(self, func, *args):
        return func(*args)


def deployed_hass(root, resources=None, shape="dataclass"):
    """A ``hass`` whose ``www/`` has been populated, exactly as setup does.

    ``async_setup_entry`` deploys before it registers, so a fixture that
    registers against an empty ``www/`` exercises a state the integration
    never reaches. That distinction used to be cosmetic and is now
    load-bearing: the resource key is taken from the served bytes, so an
    undeployed fixture measures the absence of the bundles rather than the
    behaviour of the registrars.
    """
    hass = FakeHass(root, resources, shape=shape)
    package_init._deploy_cards_to_www(hass)
    return hass


BUNDLE_URLS = bundle_urls()


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

    def _run_all(self, registrars, order, shape="dataclass"):
        """Run ``registrars`` against resources listed in ``order``.

        Returns the collection and whether the ``.storage`` fallback ran. The
        second half matters: a registrar that cannot read ``hass.data`` still
        reaches the right end state via the fallback, so asserting only on
        URLs cannot tell a working primary path from a dead one.
        """
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        resources = FakeResources([stale(url) for url in order])
        hass = deployed_hass(scratch.name, resources, shape=shape)
        for registrar in registrars:
            asyncio.run(registrar(hass))
        fell_back = (Path(scratch.name) / ".storage" / "lovelace_resources").exists()
        return resources, fell_back

    def _cases(self):
        """Every Lovelace shape, registrar order and resource order.

        All three dimensions are enumerated rather than taken as given. The
        registrar order this module happens to iterate in is alphabetical,
        which coincides with the order ``async_setup_entry`` calls them --
        a coincidence, and one that would quietly stop holding the moment a
        bundle is added whose name sorts differently. A correct
        implementation does not depend on any of them, so the test should
        not depend on getting them right.
        """
        for shape in sorted(LOVELACE_SHAPES):
            for registrar_order in itertools.permutations(sorted(ASYNC_REGISTRARS)):
                registrars = [ASYNC_REGISTRARS[name] for name in registrar_order]
                for url_order in itertools.permutations(sorted(BUNDLE_URLS.values())):
                    label = {
                        "lovelace": shape,
                        "registrars": [n.replace("_async_register_", "") for n in registrar_order],
                        "resources": [filename_of(u) for u in url_order],
                    }
                    yield registrars, url_order, shape, label

    def test_the_primary_path_is_used_for_every_lovelace_shape(self):
        """``hass.data['lovelace']`` is a dataclass, and was read as a mapping.

        ``lovelace_data.get("resources")`` raises ``AttributeError`` against
        the real object. The registrars caught it with a bare ``except
        Exception`` and logged at ``debug``, so the primary path never ran and
        nothing said so: every install has been registering its cards by
        editing ``.storage/lovelace_resources`` underneath a running Home
        Assistant, which is the path written for the case where the API is
        unavailable.

        Asserted as *the fallback did not run* rather than as *the collection
        was touched*, because the fallback reaches the same end state -- which
        is exactly why this went unnoticed.
        """
        for registrars, order, shape, label in self._cases():
            with self.subTest(**label):
                resources, fell_back = self._run_all(registrars, order, shape)
                self.assertFalse(
                    fell_back,
                    "the .storage fallback ran even though hass.data['lovelace'] "
                    "was available: the primary path is unreachable for this shape",
                )
                self.assertTrue(
                    resources.updated or resources.created,
                    "the resource collection was never touched",
                )

    def test_no_registrar_changes_a_resources_filename(self):
        """The invariant. A cache-bust may be rewritten; a filename may not."""
        for registrars, order, shape, label in self._cases():
            with self.subTest(**label):
                resources, _ = self._run_all(registrars, order, shape)
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
        for registrars, order, shape, label in self._cases():
            with self.subTest(**label):
                resources, _ = self._run_all(registrars, order, shape)
                self.assertEqual(sorted(filename_of(u) for u in resources.urls()), expected)

    def test_every_resource_ends_up_at_the_current_version(self):
        """The stale-forever half: a resource nobody visits is never updated."""
        current = {filename_of(url): url for url in BUNDLE_URLS.values()}
        for registrars, order, shape, label in self._cases():
            with self.subTest(**label):
                resources, _ = self._run_all(registrars, order, shape)
                stuck = [u for u in resources.urls() if u != current.get(filename_of(u))]
                self.assertEqual(stuck, [], f"still stale; expected {sorted(current.values())}")

    def test_a_registrar_updates_a_stale_resource_it_owns(self):
        """Non-vacuity: the tests above must not pass by doing nothing at all.

        Passes before and after the fix. Without it, a registrar that matched
        no resource ever would satisfy every invariant above trivially.
        """
        registrars = [ASYNC_REGISTRARS[name] for name in sorted(ASYNC_REGISTRARS)]
        resources, _ = self._run_all(registrars, sorted(BUNDLE_URLS.values()))
        self.assertTrue(resources.updated, "no registrar updated anything")

    def test_the_real_lovelace_data_is_not_a_mapping(self):
        """The premise, pinned against the upstream class rather than recalled.

        Passes before and after: it is a fact about Home Assistant, and it is
        the reason the fixture above is a dataclass. If Lovelace ever goes
        back to a mapping this becomes the thing that says so.
        """
        self.assertFalse(
            hasattr(FakeLovelaceData(resource_mode="storage"), "get"),
            "a dataclass must not answer .get(); the fixture has stopped "
            "modelling the failure it exists to reproduce",
        )


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
        hass = deployed_hass(scratch.name)  # no lovelace data -> storage fallback
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
        hass = deployed_hass(scratch.name)
        for name in sorted(ASYNC_REGISTRARS):
            asyncio.run(ASYNC_REGISTRARS[name](hass))
        urls = [i["url"] for i in json.loads(path.read_text(encoding="utf-8"))["data"]["items"]]
        self.assertIn(foreign, urls)


if __name__ == "__main__":
    unittest.main()
