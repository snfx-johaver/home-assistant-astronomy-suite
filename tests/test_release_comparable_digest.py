"""A diagnostics report must be able to name the release it is running.

Run with: python -m unittest discover -s tests -p "test_*.py"

The defect this measures
------------------------
``diagnostics.py`` reported one digest per file and documented it as the value
to check against a published release. It is not that value, and cannot be.

A checkout with ``core.autocrlf=true`` renders tracked text files CRLF; the
blobs the delivery channel serves are LF. One commit therefore ships under two
byte-identities, and ``sha256`` names whichever one this machine happens to
hold. Two correct installs of the same release disagree, and neither is wrong
-- each is accurate about its own copy.

The consequence is not academic, and it is not symmetric. It falls entirely on
the population the module was written for. A hand-copied bundle comes out of a
Windows working tree, so it is CRLF by construction; a HACS delivery is LF. The
report could therefore identify a healthy install and not an anomalous one --
the exact install whose bytes nobody can otherwise account for is the one whose
digest matches no release on record.

How it is measured
------------------
Against bytes obtained independently of the report: the blob ``git`` holds is
what a consumer is served, so it is the reference, and nothing here recomputes
it from the fixture. The same shipped files are then written out twice, once as
the channel delivers them and once as a Windows checkout renders them, and the
report is asked to identify both.

On the control, and why these tests run against the unfixed code
----------------------------------------------------------------
Naming ``sha256_normalised`` directly would raise ``KeyError`` before the fix,
which measures the *absence of a field* rather than the defect -- a test that
can only fail by not finding something has not looked at behaviour. So the
assertions discover every digest-shaped value in an entry and ask whether the
delivered digest is among them. That question is well-formed on both sides of
the fix: before, the answer is "no, only the CRLF digest is here", printed with
both values; after, "yes". It also means a third digest field added later is
included without editing this file.

The pair of tests that matters is deliberately one assertion applied to two
renderings. Before the fix exactly one of them passes, which states the defect
more precisely than a red test on its own could: the report identifies a Linux
install and fails to identify a Windows one.

Not asserted, on purpose
------------------------
That the byte digest becomes stable across renderings. It must not. The first
twelve characters of it are the ``?v=`` cache-bust, and two renderings are two
different responses to one URL: a browser holding one cannot learn about the
other. ``test_cache_bust_coupling`` guards that from the URL side; the test
below named ``..._the_byte_digest_still_moves_...`` guards it from this side,
because "make the digest comparable" is a plausible instruction to follow one
step too far.
"""

import re
import subprocess
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import COMPONENT_DIR, ROOT, load_component_module

package_init = load_component_module("__init__")
diagnostics = load_component_module("diagnostics")

SHA256_HEX = re.compile(r"\A[0-9a-f]{64}\Z")


def delivered_bytes(filename):
    """The blob a consumer receives, read from git rather than the worktree.

    The worktree copy is the one rendering that is never delivered to anybody:
    it is whatever this machine's checkout filter produced. Reading it here
    would make the reference and the subject the same object on Linux and two
    different objects on Windows, so the test would pass everywhere and mean
    something different in each place.

    The index is read rather than ``HEAD`` so a staged change is measured
    before it is committed -- and because the index is what the next commit
    delivers.
    """
    relative = (COMPONENT_DIR / filename).relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "cat-file", "blob", f":{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


DELIVERED = {name: delivered_bytes(name) for name in package_init.DEPLOYED_FILENAMES}

TEXT = [name for name, data in DELIVERED.items() if b"\x00" not in data]
BINARY = [name for name, data in DELIVERED.items() if b"\x00" in data]


def as_delivered(data):
    return data


def as_windows_checkout(data):
    """What ``core.autocrlf=true`` writes into a working tree.

    Binary is left alone because the checkout filter leaves it alone; a
    fixture that reflowed an image would be testing a file no machine has.
    """
    if b"\x00" in data:
        return data
    return data.replace(b"\n", b"\r\n")


def install(root, render):
    """A miniature install of the real shipped files, in one rendering.

    Enumerated from ``DEPLOYED_FILENAMES``, so a fourth file is covered here
    the day it is added rather than the day someone remembers this file.
    """
    package_dir = Path(root) / "package"
    www_dir = Path(root) / "www"
    package_dir.mkdir()
    www_dir.mkdir()
    for name, data in DELIVERED.items():
        payload = render(data)
        (package_dir / name).write_bytes(payload)
        (www_dir / name).write_bytes(payload)
    return package_dir, www_dir


def report_for(render):
    with tempfile.TemporaryDirectory() as tmp:
        return diagnostics.build_report(*install(tmp, render), [])


def sides(entry):
    """Every copy an entry describes, discovered rather than named."""
    return {
        key: value
        for key, value in entry.items()
        if isinstance(value, dict) and value.get("present")
    }


def digests_in(measurement):
    """Every digest-shaped value in one file's measurement.

    Discovered by shape. The point of the fix is that a report needs more than
    one digest, so a test that named the one it wanted would have to be edited
    every time that set changed -- and the reason to change it is exactly the
    reason to distrust it.
    """
    return {
        key: value
        for key, value in measurement.items()
        if isinstance(value, str) and SHA256_HEX.match(value)
    }


class FixtureTests(unittest.TestCase):
    """Non-vacuity for everything below: the fixture must exercise the split."""

    def test_the_shipped_files_include_text_and_binary(self):
        self.assertGreaterEqual(len(TEXT), 2, TEXT)
        self.assertGreaterEqual(len(BINARY), 1, BINARY)

    def test_the_delivered_blobs_carry_no_carriage_returns(self):
        """The rendering below is only faithful if it starts from LF.

        If a blob already held CRLF, ``replace`` would produce ``\\r\\r\\n``
        and every assertion here would be about a file no channel serves.
        """
        offenders = {n: DELIVERED[n].count(b"\r") for n in TEXT if b"\r" in DELIVERED[n]}
        self.assertEqual(offenders, {}, offenders)

    def test_the_two_renderings_are_actually_different(self):
        """Passes before and after. Without it the comparison could be a no-op."""
        for name in TEXT:
            with self.subTest(name):
                self.assertNotEqual(
                    as_windows_checkout(DELIVERED[name]),
                    DELIVERED[name],
                    f"{name} renders identically both ways, so it cannot "
                    "demonstrate anything about rendering",
                )


class ReleaseComparabilityTests(unittest.TestCase):
    """One question, asked of two installs of the same release."""

    def assert_names_the_release(self, render, label):
        report = report_for(render)
        for name in package_init.DEPLOYED_FILENAMES:
            expected = sha256(DELIVERED[name]).hexdigest()
            for side, measurement in sides(report["files"][name]).items():
                with self.subTest(file=name, copy=side):
                    found = digests_in(measurement)
                    self.assertIn(
                        expected,
                        set(found.values()),
                        f"{name} ({side}) on a {label} install reports "
                        f"{found} and none of those is the delivered digest "
                        f"{expected!r}, so this install cannot be matched to "
                        "the release it is running",
                    )

    def test_an_install_as_delivered_names_the_release(self):
        """Non-vacuity. Passes before and after.

        The byte digest is already the delivered digest when nothing reflowed
        the file, so this half of the property was never broken -- which is
        why the defect survived review, and why it is worth showing the suite
        discriminating rather than going uniformly red.
        """
        self.assert_names_the_release(as_delivered, "as-delivered")

    def test_an_install_rendered_by_a_windows_checkout_names_the_release(self):
        """The defect. Identical assertion, one rendering later."""
        self.assert_names_the_release(as_windows_checkout, "Windows-checkout")

    def test_one_field_identifies_the_release_for_every_file(self):
        """A consumer needs a single rule, not a rule with an exception.

        The tests above accept the delivered digest appearing under *any*
        field, which a report could satisfy by answering under one name for
        text and another for images. That would be correct and close to
        useless: whoever compares an install against a release has to write
        the comparison once, and a field that is null for some files means the
        obvious implementation compares a null against a digest and calls a
        healthy install a mismatch.

        So this asks for something stronger and states the design decision as
        a measurement rather than as a comment: there must exist one field
        name that carries the delivered digest for every file in the report,
        under both renderings. Nothing here says which name.
        """
        for render, label in (
            (as_delivered, "as-delivered"),
            (as_windows_checkout, "Windows-checkout"),
        ):
            report = report_for(render)
            universal = None
            witness = {}
            for name in package_init.DEPLOYED_FILENAMES:
                expected = sha256(DELIVERED[name]).hexdigest()
                for side, measurement in sides(report["files"][name]).items():
                    matching = {
                        key
                        for key, value in digests_in(measurement).items()
                        if value == expected
                    }
                    witness[f"{name} [{side}]"] = sorted(matching)
                    universal = matching if universal is None else universal & matching
            with self.subTest(label):
                self.assertTrue(
                    universal,
                    f"no single field names the release on a {label} install, "
                    f"so a consumer needs a per-file rule: {witness}",
                )


class RenderingInvarianceTests(unittest.TestCase):
    """The property stated directly, without an external reference."""

    def setUp(self):
        self.delivered = report_for(as_delivered)["files"]
        self.windows = report_for(as_windows_checkout)["files"]

    def digests(self, files, name):
        return digests_in(files[name]["installed"])

    def test_some_digest_is_invariant_under_the_rendering(self):
        """A report of one release must agree with itself across transports."""
        for name in TEXT:
            with self.subTest(name):
                delivered = self.digests(self.delivered, name)
                windows = self.digests(self.windows, name)
                agreeing = {
                    key
                    for key in delivered.keys() & windows.keys()
                    if delivered[key] == windows[key]
                }
                self.assertTrue(
                    agreeing,
                    f"{name}: no field survives the rendering. "
                    f"as delivered {delivered}, from a Windows checkout "
                    f"{windows}. Two installs of one release have nothing "
                    "in common to compare.",
                )

    def test_the_byte_digest_still_moves_with_the_rendering(self):
        """Passes before and after, and is the reason this is an added field.

        The ``?v=`` cache-bust is the first twelve characters of the byte
        digest. If making the report comparable were done by normalising that
        digest, two renderings -- several kilobytes apart on the wire -- would
        share a URL, and a browser holding one could never be told about the
        other. The instruction "make the digest comparable" has an obvious
        wrong reading and this is what stops it.
        """
        for name in TEXT:
            with self.subTest(name):
                self.assertNotEqual(
                    self.delivered[name]["installed"]["sha256"],
                    self.windows[name]["installed"]["sha256"],
                    f"{name} has the same byte digest in two renderings that "
                    "differ on the wire",
                )

    def test_a_binary_file_is_untouched_by_either_rendering(self):
        """Passes before and after. Guards a normaliser that rewrites images.

        A PNG's signature contains a CRLF pair. Collapsing it would describe a
        file that exists on no disk, and would do it while reporting success.
        """
        for name in BINARY:
            with self.subTest(name):
                self.assertEqual(
                    self.delivered[name]["installed"],
                    self.windows[name]["installed"],
                    f"{name} is binary and was altered by a rendering",
                )
                self.assertEqual(
                    self.delivered[name]["installed"]["sha256"],
                    sha256(DELIVERED[name]).hexdigest(),
                )

    def test_the_report_still_covers_every_deployed_file(self):
        """Passes before and after: the enumeration guard for both reports."""
        for label, files in (("delivered", self.delivered), ("windows", self.windows)):
            with self.subTest(label):
                self.assertEqual(
                    set(files), set(package_init.DEPLOYED_FILENAMES)
                )


if __name__ == "__main__":
    unittest.main()
