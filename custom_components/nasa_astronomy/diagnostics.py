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

Three fields deserve explanation:

``sha256``
    The full digest of the file as it sits on disk. The first twelve
    characters are the ``?v=`` cache-bust the integration serves, so this
    identifies the exact object a browser is being handed. A digest
    authenticates bytes, not provenance -- which is why it is reported
    *beside* the filename and the directory it came from rather than on its
    own.

    It cannot be compared against a published release, and an earlier version
    of this paragraph claimed it could. A checkout with ``core.autocrlf=true``
    renders a tracked text file CRLF, while the blob the delivery channel
    serves is LF. One commit therefore has two byte-identities and two
    digests, neither of them wrong -- each is correct about its own copy. The
    comparison fails hardest on precisely the population this module exists
    for: a hand-copied Windows install is CRLF by construction, so the one
    install whose bytes most need identifying is the one whose digest cannot
    be looked up.

``sha256_normalised``
    The same file with CRLF collapsed to LF. This is the digest to compare
    against a release, because it survives the rendering a delivery path
    imposes -- and it is present for *every* file, images included, which are
    reported unmodified rather than skipped. One comparison then answers "is
    this install the published release" for the whole report. A null for
    binaries would make that one comparison plus an exception, and the
    exception is the part a consumer gets wrong: comparing a null against a
    real digest reports a mismatch on every healthy install.

    Reported *as well as* ``sha256``, not instead of it, because the two
    answer different questions and neither answers both: the byte digest names
    the object a browser is handed, the normalised digest names the release
    that object came from. The same reasoning is why the ``?v=`` cache-bust
    must keep using the byte digest -- two renderings are two different
    responses to one URL, several kilobytes apart, and a browser holding one
    has no way to learn about the other.

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
    BUNDLE_FILENAMES,
    DEPLOYED_FILENAMES,
    deployed_dir,
    resource_url,
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


def normalised_digest(data: bytes) -> str:
    """The digest of ``data`` as the delivery channel holds it.

    A content digest is only comparable *within* one transport. Git's
    ``autocrlf`` smudge rewrites LF to CRLF on checkout, so the same commit
    produces different bytes -- and different digests -- on a Windows working
    tree than on the blob a user is served. Collapsing CRLF back to LF undoes
    that, giving a value two installs can compare even when they were
    delivered by different routes.

    The inversion is exact rather than approximate, and the repository is what
    makes it so: ``test_delivered_bytes`` pins every tracked text blob to LF,
    so any CRLF in a checkout was introduced by the smudge and removing it
    returns the delivered bytes. That is a property of this repository, not of
    line endings in general -- against a project that commits CRLF this would
    be a lossy rewrite rather than an inverse.

    Binary is never rewritten: a byte pair that happens to look like a line
    ending is data there, and a PNG signature contains one. But it is still
    *reported*, as the unmodified digest, rather than skipped and left null.
    That is the difference between a rule and a rule with an exception. The
    use of this field is "does this install match the release", and a consumer
    answering it applies one comparison to every file; a null for images means
    the obvious consumer compares nothing against something and reports a
    mismatch on every healthy install. Whether a file was reflowed is a
    question ``line_endings`` already answers, so nothing is lost by declining
    to answer it twice here.

    Binary is detected through ``line_endings`` rather than by a second test
    of its own, so the classifier and the normaliser cannot come to disagree
    about a file. A suffix list, or a second NUL check, would be a place for
    them to.
    """
    if line_endings(data) is not None:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


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
        "sha256_normalised": normalised_digest(data),
        "line_endings": line_endings(data),
    }


def build_report(
    package_dir: Path, www_dir: Path, resource_urls: list[str]
) -> dict[str, Any]:
    """The report, as a plain function of two directories and the URLs.

    Takes paths rather than ``hass`` so it can be exercised against fixtures
    on disk without standing up a Home Assistant. The URLs are passed in for
    the same reason, and because building them is the caller's job: they are a
    function of the served directory, not of this report.
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
        "resource_urls": resource_urls,
        "files": files,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    The report reads several files, including a half-megabyte image, so it
    runs in the executor rather than on the event loop. Building the URLs
    hashes the served bundles, so that happens in the executor too.
    """

    def report() -> dict[str, Any]:
        return build_report(
            Path(__file__).parent,
            deployed_dir(hass),
            [resource_url(hass, name) for name in BUNDLE_FILENAMES],
        )

    return await hass.async_add_executor_job(report)
