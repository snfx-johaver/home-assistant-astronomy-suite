"""What gets delivered is the blob, and the blob's line endings are load-bearing.

Run with: python -m unittest discover -s tests -p "test_*.py"

HACS installs an integration by fetching the repository tree from GitHub, so
what lands in ``custom_components/nasa_astronomy/`` on a user's machine is the
*blob* -- not anyone's working tree. Git renders blobs differently per
checkout: with ``core.autocrlf=true`` a text file arrives CRLF, without it LF.
This repository has no ``.gitattributes``, so nothing declares which rendering
is canonical; the blobs are LF today because every commit so far happened to
normalise on the way in.

Why that assumption is worth a test rather than a comment
--------------------------------------------------------
Two mechanisms depend on it, and both fail quietly if it stops holding.

1. **The cache-bust key.** ``_cache_bust_for`` digests the bundle's bytes as
   delivered. A commit that flips the bundles to CRLF adds ~3 kB and changes
   every install's key at once -- every browser re-downloads, and the diff
   that caused it shows no content change at all.

2. **Provenance.** Line endings are the only surviving evidence of *how* a
   file arrived. On a live install we found ten integration files at LF and
   the two card bundles at CRLF, with a nine-hour mtime gap: the bundles had
   been hand-copied out of a Windows working tree onto a HACS-delivered
   install, and the line endings alone established it -- no logs, no history.
   That diagnostic exists only while the delivery channel's rendering is
   uniform. Commit one CRLF blob and it is gone, permanently and silently.

This test reads blobs via ``git cat-file``, never the working tree
------------------------------------------------------------------
On a CRLF checkout every text file on disk carries CR while its blob does
not, so a probe that read the working tree would be red on Windows and green
on Linux while measuring nothing about what users receive. That is not a
hypothetical: it is exactly the confusion that produced a published digest
belonging to a rendering rather than to a release.

Known limit, stated rather than implied: ``test_the_probe_reads_the_blob``
can only *prove* the distinction on a checkout where the two renderings
differ. On a LF checkout the two are equal and it degrades to a tautology.
The CR sweep itself is unaffected -- it is exact on every platform.
"""

import subprocess
import unittest
from pathlib import Path

from test_version_literals import ROOT, is_declared_binary, tracked_files


def blob_bytes(relative_path, ref="HEAD"):
    """The bytes git would hand a consumer, independent of this checkout."""
    result = subprocess.run(
        ["git", "cat-file", "-p", f"{ref}:{relative_path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


def carriage_returns(data):
    """Count CR bytes. A pure function so it can be tested on synthetic input.

    The sweep below quantifies over the repository, whose current answer is
    zero; a detector that always returned zero would satisfy it forever. This
    is the half that can be checked against known inputs instead.
    """
    return data.count(b"\r")


def delivered_text_files():
    return [name for name in tracked_files() if not is_declared_binary(name)]


class DeliveredLineEndingTests(unittest.TestCase):
    def test_no_delivered_text_file_carries_carriage_returns(self):
        """The invariant. Enumerated from git, not listed here.

        A file added later is covered without anyone remembering this file
        exists, which is the failure mode being guarded against.
        """
        offenders = {}
        for name in delivered_text_files():
            count = carriage_returns(blob_bytes(name))
            if count:
                offenders[name] = count
        self.assertEqual(
            offenders,
            {},
            "these blobs carry CR, so they were committed from a checkout "
            "that does not normalise line endings. Every install now "
            "receives different bytes than before for no content change: "
            "the cache-bust key moves for all of them at once, and the "
            "line-ending provenance signal is destroyed. Fix the commit "
            "rather than this test, or add a .gitattributes that declares "
            "the intent",
        )

    def test_the_sweep_read_something(self):
        """Non-vacuity. Zero files is the one answer that is never legitimate.

        Passes before and after any fix here. Without it, an empty universe
        -- a broken ``tracked_files()``, a classification that swallowed
        everything -- would satisfy the assertion above by having nothing to
        disagree with.
        """
        files = delivered_text_files()
        self.assertGreater(len(files), 10, files)

    def test_the_detector_is_not_a_constant(self):
        """The sweep's current answer is zero; so is a broken detector's.

        Checked against synthetic bytes, so this is exact and independent of
        the repository's contents.
        """
        self.assertEqual(carriage_returns(b"a\nb\nc\n"), 0)
        self.assertEqual(carriage_returns(b"a\r\nb\r\nc\r\n"), 3)
        self.assertEqual(carriage_returns(b"bare \r return"), 1)
        self.assertEqual(carriage_returns(b""), 0)

    def test_the_probe_reads_the_blob(self):
        """Guards against 'simplify this to Path.read_bytes()'.

        That refactor is inviting -- it is shorter, and it is green on Linux
        CI forever. It would make the whole module report on the developer's
        checkout instead of on what users receive.

        On a checkout whose rendering differs from the blob (autocrlf on),
        this is a real discrimination. On one where they agree it degrades to
        a tautology, and says so rather than pretending otherwise.
        """
        sample = "custom_components/nasa_astronomy/manifest.json"
        self.assertIn(sample, delivered_text_files(), "sample file is not tracked")

        blob = blob_bytes(sample)
        worktree = (ROOT / Path(sample)).read_bytes()

        if blob == worktree:
            self.assertEqual(
                carriage_returns(worktree),
                0,
                "checkout and blob agree, so this checkout renders LF; the "
                "distinction this test guards cannot be exercised here",
            )
        else:
            self.assertNotEqual(
                carriage_returns(worktree),
                carriage_returns(blob),
                "checkout and blob differ by something other than line "
                "endings, which this probe does not model",
            )
            self.assertEqual(carriage_returns(blob), 0)


if __name__ == "__main__":
    unittest.main()
