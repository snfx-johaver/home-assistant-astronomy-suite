"""Diagnostics: what is actually on disk, measured rather than claimed.

Three mechanisms report a version for this integration and none of them
measures the files a browser receives:

* ``manifest.json`` is what a release wrote. It is a claim about intent.
* ``sw_version`` on the device is that same claim, read back.
* HACS's ``version_installed`` is a record of what HACS itself did. It is a
  log of the manager's own actions, so anything that writes to the install
  directory by another route -- a hand-copied bundle, a local build, an
  unpacked zip -- leaves it untouched. HACS then reports "up to date" and is
  correct about its own history while being wrong about the artefact.

A real install has been observed in exactly that state: ``manifest.json`` and
HACS agreeing on a version whose bundles were nine releases old, while both
card bundles on disk were a later release's, written eleven hours after the
install. Nothing in the system could see it. It took reading the files over
SMB.

(Deliberately described rather than quoted. A version-shaped literal in a
shipped file reads as authoritative even inside a docstring, and the repo's
literal sweep is right to refuse one -- it caught this paragraph.)

This report measures the bytes instead, so the same question is answerable
from a diagnostics download.

Two fields deserve explanation:

``sha256``
    The full digest of the file as it sits on disk. The first twelve
    characters are the ``?v=`` cache-bust the integration serves, so this
    identifies the exact object a browser is being handed and can be compared
    against any published release. A digest authenticates bytes, not
    provenance -- which is why it is reported *beside* the filename and the
    directory it came from rather than on its own.

``line_endings``
    Provenance, and the only evidence that survives a hand-copy. HACS installs
    files from GitHub blobs, which are LF. CRLF cannot arrive that way, so a
    CRLF bundle sitting next to LF Python files did not come through the
    delivery channel -- it was copied out of a Windows working tree. That is
    precisely how the install above was diagnosed.

No config entry data is included. It holds API keys, reporting it would
require a redaction list, and a redaction list is one more thing that can
silently fall behind the data it redacts. The question here is about bytes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import (
    CARDS_LOCAL_URL,
    DEEPSKY_CARDS_LOCAL_URL,
    DEPLOYED_FILENAMES,
    deployed_dir,
)
from .const import INTEGRATION_VERSION


def line_endings(data: bytes) -> str | None:
    """Classify a payload's line endings, or ``None`` if it is not text.

    Binary is detected by content rather than by file extension, because a
    suffix list is a second declaration that can disagree with the first. A
    NUL byte is the standard heuristic and every image this integration ships
    carries one in its header.
    """
    if b"\x00" in data:
        return None
    crlf = data.count(b"\r\n")
    bare_lf = data.count(b"\n") - crlf
    bare_cr = data.count(b"\r") - crlf
    if not (crlf or bare_lf or bare_cr):
        return "none"
    if crlf and not bare_lf and not bare_cr:
        return "crlf"
    if bare_lf and not crlf and not bare_cr:
        return "lf"
    return "mixed"


def describe(path: Path) -> dict[str, Any]:
    """Measure one file. Absence is a result, not an error."""
    try:
        data = path.read_bytes()
    except OSError as err:
        return {"present": False, "error": type(err).__name__}
    return {
        "present": True,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "line_endings": line_endings(data),
    }


def build_report(package_dir: Path, www_dir: Path) -> dict[str, Any]:
    """The report, as a plain function of two directories.

    Takes paths rather than ``hass`` so it can be exercised against fixtures
    on disk without standing up a Home Assistant.
    """
    files: dict[str, Any] = {}
    for filename in DEPLOYED_FILENAMES:
        installed = describe(package_dir / filename)
        served = describe(www_dir / filename)
        installed_digest = installed.get("sha256")
        files[filename] = {
            # What is in the integration's own directory: whatever HACS, a
            # zip, or a hand-copy last put there.
            "installed": installed,
            # What was copied into ``www/`` and is actually served over HTTP.
            "served": served,
            # A failed or partial copy leaves these disagreeing, and the
            # served file is the one a browser gets.
            "served_matches_installed": (
                installed_digest is not None
                and installed_digest == served.get("sha256")
            ),
        }
    return {
        "integration_version": INTEGRATION_VERSION,
        "deployed_directory": str(www_dir),
        "resource_urls": [CARDS_LOCAL_URL, DEEPSKY_CARDS_LOCAL_URL],
        "files": files,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The report reads several files, including a half-megabyte image, so it
    runs in the executor rather than on the event loop.
    """
    return await hass.async_add_executor_job(
        build_report, Path(__file__).parent, deployed_dir(hass)
    )
