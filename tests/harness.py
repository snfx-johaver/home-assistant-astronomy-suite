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
import atexit
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The component tree under test. Overridable so a test can point the loader at
# a *perturbed copy* of the component and observe what the suite does against
# it. That is the only way to run a counterfactual control here: the defects
# these tests guard against are ones the current tree does not have, so the
# only way to show an assertion can still catch them is to rebuild the defect
# somewhere safe and watch the assertion go red.
#
# It is an environment variable rather than an argument because the module
# graph is resolved at import time, through `from .const import ...`, so the
# choice has to be made before any component module is imported -- which in
# practice means before this module's importers run, i.e. in a subprocess.
# Defaults to the real tree, so nothing changes for an ordinary run.
COMPONENT_DIR = Path(
    os.environ.get(
        "NASA_ASTRONOMY_COMPONENT_DIR",
        ROOT / "custom_components" / "nasa_astronomy",
    )
).resolve()

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


class _CoordinatorEntity(_StubBase):
    """Stand-in for ``CoordinatorEntity``, which is generic *and* stateful.

    The real base class assigns ``self.coordinator`` in ``__init__``. This
    integration reads ``self.coordinator`` in 37 places and assigns it in
    none, so a stub that accepted the argument and dropped it would make
    every entity property raise ``AttributeError`` under test while working
    correctly in production -- a false red aimed at code that is right, and
    the kind a test author papers over by assigning the attribute in the
    test rather than in the stub.
    """

    def __init__(self, coordinator=None, context=None):
        self.coordinator = coordinator
        self.coordinator_context = context


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
        CoordinatorEntity=_CoordinatorEntity,
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


def _populate_package_alias(module):
    """Make ``from . import X`` resolve, the way it does in a real package.

    ``__init__.py`` is loaded under a qualified name so it can be cached and
    reloaded like any other module, which leaves ``sys.modules`` holding an
    *empty* package alias. Real integrations import from their own package --
    ``diagnostics.py`` does -- and against an empty alias that raises
    ``ImportError`` for a name that exists perfectly well in production.

    Worth stating plainly, because the opposite mistake was made here before:
    a stub is a claim about production. One that is *kinder* than production
    manufactures coverage; one that is *harsher* invents failures and pushes
    the code towards contortions that exist only to satisfy the harness.
    Mirror the executed namespace onto the alias so neither happens.
    """
    package = sys.modules[PACKAGE_ALIAS]
    for name, value in vars(module).items():
        if not name.startswith("__"):
            setattr(package, name, value)


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
    # Registering before execution is required: ``from .const import DOMAIN``
    # resolves against ``sys.modules`` while the module is still running. But
    # a failure after this point must not leave the half-built module behind,
    # because the cache hit above would then hand it to every later caller --
    # who sees an empty module and no error at all. That is not a missing
    # answer, it is a confident wrong one: the first caller gets the real
    # exception and everyone after gets silence, or ``AttributeError: module
    # has no attribute X`` pointing at the wrong module entirely.
    sys.modules[qualified] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[qualified]
        raise
    if parent == PACKAGE_ALIAS and module_name == "__init__":
        _populate_package_alias(module)
    return module


class _MinimalConfig:
    def __init__(self, root):
        self.root = Path(root)

    def path(self, *parts):
        return str(self.root.joinpath(*parts))


class MinimalHass:
    """Just enough ``hass`` to deploy the shipped files and build their URLs.

    ``config.path`` is the only Home Assistant surface either of those touches,
    so this stub stays deliberately this small; a richer one would be a second
    account of their requirements, free to drift from the first.
    """

    def __init__(self, root):
        self.config = _MinimalConfig(root)
        self.data = {}

    async def async_add_executor_job(self, func, *args):
        return func(*args)


def deployed_urls(module, root=None):
    """Every bundle URL the component would register, keyed by filename.

    A resource URL is a function of ``hass`` rather than a module constant,
    because its cache-bust names the copy under ``config/www`` -- the bytes a
    browser is actually served. Obtaining one therefore means deploying first,
    which is also the order ``async_setup_entry`` runs in.

    Creates and cleans up a scratch directory when ``root`` is omitted.
    """
    if root is None:
        root = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, root, True)
    hass = MinimalHass(root)
    module._deploy_cards_to_www(hass)
    return {
        name: module.resource_url(hass, name) for name in module.BUNDLE_FILENAMES
    }
