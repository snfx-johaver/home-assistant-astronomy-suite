"""Loads the integration's Python modules with just enough Home Assistant
stubs to import them, then hands back the modules for testing.

This is the Python counterpart to ``harness.mjs``. The card bundles need DOM
stubs to evaluate; ``sensor_deepsky`` needs Home Assistant stubs for the same
reason. Its astronomy helpers are pure stdlib maths that never touch Home
Assistant, but they live in a module whose imports do — so we stub those
imports rather than adding a Home Assistant dependency to the test run.

The component package is bound under an alias whose ``__path__`` points at the
real source directory. That resolves ``from .const import DOMAIN`` against the
real ``const.py`` without executing the package ``__init__.py``.
"""

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "nasa_astronomy"

PACKAGE_ALIAS = "nasa_astronomy_under_test"


class _StubBase:
    """Stand-in for a Home Assistant base class or annotation-only type."""

    def __init__(self, *args, **kwargs):
        pass

    def __class_getitem__(cls, item):
        return cls


class _SensorStateClass:
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"


def _register(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def install_homeassistant_stubs():
    """Register the minimal ``homeassistant.*`` surface the modules import."""
    if "homeassistant" in sys.modules:
        return

    _register("homeassistant")
    _register("homeassistant.components")
    _register(
        "homeassistant.components.sensor",
        SensorEntity=type("SensorEntity", (_StubBase,), {}),
        SensorStateClass=_SensorStateClass,
        SensorDeviceClass=type("SensorDeviceClass", (_StubBase,), {}),
    )
    _register("homeassistant.config_entries", ConfigEntry=_StubBase)
    _register("homeassistant.const", DEGREE="\u00b0")
    _register("homeassistant.core", HomeAssistant=_StubBase, callback=lambda fn: fn)
    _register("homeassistant.helpers")
    _register("homeassistant.helpers.entity_platform", AddEntitiesCallback=_StubBase)
    _register(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=type("CoordinatorEntity", (_StubBase,), {}),
        DataUpdateCoordinator=type("DataUpdateCoordinator", (_StubBase,), {}),
        UpdateFailed=type("UpdateFailed", (Exception,), {}),
    )


def _ensure_package_alias():
    if PACKAGE_ALIAS in sys.modules:
        return
    package = types.ModuleType(PACKAGE_ALIAS)
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules[PACKAGE_ALIAS] = package


def load_component_module(module_name, *, subpackage=None):
    """Import one module from ``custom_components/nasa_astronomy``.

    ``subpackage`` selects a nested directory, e.g. ``"providers"``.
    """
    install_homeassistant_stubs()
    _ensure_package_alias()

    if subpackage:
        parent = f"{PACKAGE_ALIAS}.{subpackage}"
        if parent not in sys.modules:
            nested = types.ModuleType(parent)
            nested.__path__ = [str(COMPONENT_DIR / subpackage)]
            sys.modules[parent] = nested
        path = COMPONENT_DIR / subpackage / f"{module_name}.py"
    else:
        parent = PACKAGE_ALIAS
        path = COMPONENT_DIR / f"{module_name}.py"

    qualified = f"{parent}.{module_name}"
    if qualified in sys.modules:
        return sys.modules[qualified]

    spec = importlib.util.spec_from_file_location(qualified, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    return module
