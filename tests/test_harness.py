"""Tests for the test harness itself.

``harness.py`` had no tests. It is the one module in the Python suite that
exists purely so other modules can run, and every other test quantifies over
what it stubs -- which makes it the widest unasserted surface here, not the
narrowest.

Two things are checked, and they are different in kind:

* **A fault must stay a fault.** ``load_component_module`` registers a module
  in ``sys.modules`` before executing it, which relative imports require. If
  execution then failed, the half-built module stayed cached and every later
  caller got it back with no error -- silence in place of a fault, and a
  confident empty module in place of a missing one.

* **A stub must not be stricter than the thing it stands for.** A stub that
  drops state the real base class sets produces a false red aimed at correct
  code. The usual repair is to assign the attribute in the *test*, which
  moves the divergence somewhere even harder to see.

WHAT THIS MODULE DELIBERATELY DOES NOT CLAIM
--------------------------------------------
It does not assert that the stubs are faithful in general. They are not, and
they are not meant to be -- they exist to make imports resolve. Faithfulness
was *measured* rather than assumed: replacing each stub with a closer model
of Home Assistant (``CoordinatorEntity`` generic and stateful,
``SensorEntityDescription`` frozen with a required ``key``,
``async_get_clientsession`` returning a session, ``Platform`` rejecting
unknown members) left all tests green. So no test's pass currently depends on
a stub being more permissive than reality. That is a measurement with a date
on it, not a property, which is why it is recorded here rather than asserted.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402
    COMPONENT_DIR,
    PACKAGE_ALIAS,
    install_homeassistant_stubs,
    load_component_module,
)

BROKEN_MODULE = "harness_probe_deliberately_broken"


class FailedImportTests(unittest.TestCase):
    """A module that fails to import must fail every time it is asked for."""

    def setUp(self):
        self.path = COMPONENT_DIR / f"{BROKEN_MODULE}.py"
        self.path.write_text(
            "raise RuntimeError('deliberate failure: harness cache probe')\n",
            encoding="utf-8",
        )
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.path.unlink(missing_ok=True)
        sys.modules.pop(f"{PACKAGE_ALIAS}.{BROKEN_MODULE}", None)

    def test_a_failed_import_is_not_cached(self):
        """The second load must raise too, not return an empty husk.

        Before this was fixed the second call returned a module object with
        an empty namespace and raised nothing, so a caller that handles
        import errors per item -- ``collect_device_info_payloads`` does
        exactly that -- reported the true cause once and then a string of
        ``AttributeError: module has no attribute X`` for everything after
        it, pointing at the wrong module.

        Measured while probing an unrelated question: 7 reported errors, of
        which 2 were real and 5 were echoes.
        """
        with self.assertRaises(RuntimeError):
            load_component_module(BROKEN_MODULE)

        with self.assertRaises(
            RuntimeError,
            msg="the second load did not raise, so the failed import was "
            "served from cache: callers after the first see an empty module "
            "and no error",
        ):
            load_component_module(BROKEN_MODULE)

    def test_a_failed_import_leaves_no_entry_behind(self):
        """The mechanism, checked directly rather than through its symptom."""
        with self.assertRaises(RuntimeError):
            load_component_module(BROKEN_MODULE)
        # Filtered to a short list rather than asserting against sys.modules
        # itself: assertNotIn would print the entire module table on failure,
        # which buries the one name that matters.
        still_registered = [
            name for name in sys.modules if name.endswith(f".{BROKEN_MODULE}")
        ]
        self.assertEqual(
            [],
            still_registered,
            "a module that failed to execute is still registered, so the "
            "cache hit in load_component_module will serve it",
        )

    def test_a_working_import_still_caches(self):
        """Non-vacuity: passes before and after, so the suite is discriminating.

        Deleting the failed entry must not disturb the ordinary path -- the
        cache is what keeps repeated loads returning the same module object.
        """
        first = load_component_module("const")
        second = load_component_module("const")
        self.assertIs(first, second)


class StubFidelityTests(unittest.TestCase):
    """Where a stub does model the real class, it must not model it wrongly."""

    def test_coordinator_entity_assigns_the_coordinator(self):
        """Real ``CoordinatorEntity.__init__`` sets ``self.coordinator``.

        The integration reads ``self.coordinator`` in 37 places and assigns
        it in none, so a stub that accepted and dropped it would fail every
        such read under test while production worked -- a false red, and one
        whose natural repair is to assign the attribute in the test.
        """
        install_homeassistant_stubs()
        from homeassistant.helpers.update_coordinator import CoordinatorEntity

        marker = object()
        self.assertIs(CoordinatorEntity(marker).coordinator, marker)

    def test_coordinator_entity_is_still_subscriptable(self):
        """It is generic in real Home Assistant, and the source relies on that.

        ``class NasaApodCamera(CoordinatorEntity[NasaDataCoordinator], Camera)``
        is evaluated at import. A "more faithful" stub that dropped
        ``__class_getitem__`` would break every camera and sensor module --
        which is how the first draft of this measurement went wrong.
        """
        install_homeassistant_stubs()
        from homeassistant.helpers.update_coordinator import CoordinatorEntity

        self.assertIsNotNone(CoordinatorEntity[int])


if __name__ == "__main__":
    unittest.main()
