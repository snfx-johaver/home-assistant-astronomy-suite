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
    # Bind the submodule onto its parent. Seeding ``sys.modules`` by hand skips
    # the step the real import machinery does here, which breaks
    # ``from homeassistant.helpers import config_validation``.
    parent_name, _, child = name.rpartition(".")
    if parent_name and parent_name in sys.modules:
        setattr(sys.modules[parent_name], child, module)
    return module


class _Platform:
    """Stand-in for the ``Platform`` enum, which is used for the platform list."""

    SENSOR = "sensor"
    CAMERA = "camera"
    BINARY_SENSOR = "binary_sensor"


class _EntityDescription(_StubBase):
    """Stand-in for ``SensorEntityDescription``, which is a keyword dataclass.

    The real class stores every keyword as an attribute, and ``sensor.py``
    reads ``description.key`` back out, so the stub has to keep them.
    """

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def install_homeassistant_stubs():
    """Register the minimal ``homeassistant.*`` surface the modules import."""
    if "homeassistant" in sys.modules:
        return

    _register("homeassistant")
    _register("homeassistant.components")
    _register("homeassistant.components.camera", Camera=type("Camera", (_StubBase,), {}))
    _register(
        "homeassistant.components.sensor",
        SensorEntity=type("SensorEntity", (_StubBase,), {}),
        SensorStateClass=_SensorStateClass,
        SensorDeviceClass=type("SensorDeviceClass", (_StubBase,), {}),
        SensorEntityDescription=_EntityDescription,
    )
    _register("homeassistant.config_entries", ConfigEntry=_StubBase)
    _register(
        "homeassistant.const",
        DEGREE="\u00b0",
        CONF_API_KEY="api_key",
        Platform=_Platform,
    )
    _register("homeassistant.core", HomeAssistant=_StubBase, callback=lambda fn: fn)
    _register("homeassistant.helpers")
    _register(
        "homeassistant.helpers.config_validation",
        config_entry_only_config_schema=lambda domain: {"domain": domain},
    )
    _register(
        "homeassistant.helpers.aiohttp_client",
        async_get_clientsession=lambda *args, **kwargs: None,
    )
    _register("homeassistant.helpers.entity_platform", AddEntitiesCallback=_StubBase)
    _register(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=type("CoordinatorEntity", (_StubBase,), {}),
        DataUpdateCoordinator=type("DataUpdateCoordinator", (_StubBase,), {}),
        UpdateFailed=type("UpdateFailed", (Exception,), {}),
    )

    # ``aiohttp`` is a third-party import, not a Home Assistant one, but the
    # same reasoning applies: ``camera.py`` and ``coordinator.py`` import it at
    # module scope purely to make network calls the tests never reach. Stubbing
    # it keeps the test run on the standard library, which is what CI installs.
    if "aiohttp" not in sys.modules:
        _register(
            "aiohttp",
            ClientSession=_StubBase,
            ClientError=type("ClientError", (Exception,), {}),
            ClientTimeout=_StubBase,
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
