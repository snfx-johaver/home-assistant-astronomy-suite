"""A filename that asserts a property must be measured against the property.

``icon@2x.png`` and ``logo@2x.png`` were 256x256 -- byte-identical to the 1x
files they claimed to be double. The suffix is a numeric claim about pixel
dimensions, and nothing in this repository had ever checked it.

That is worse than redundancy. A consumer honouring ``@2x`` renders a 256 image
into a 512 slot, so the file it was told is higher-resolution produces a
*blurrier* result than the 1x would have. The asset was actively worse than
absent, and being byte-identical to the 1x is exactly why nobody noticed: every
comparison anyone would casually run -- does it exist, does it open, does it
look right -- passes.

The general form is the point, and it is why this module is written against a
suffix table rather than against two deleted files: ``@2x``, ``.min.js``,
``-compressed``, ``-optimised``, ``-thumb`` are all assertions in a filename,
and a filename is not verified by anything. Whenever one is introduced here it
has to arrive with the check that makes it falsifiable.

WHY THE CHECKER IS EXERCISED AGAINST SYNTHESISED FILES
------------------------------------------------------
Once the false ``@2x`` files were deleted, every assertion about scale suffixes
began quantifying over an empty set: there is no file in this repository whose
name contains ``@2x``, so the loops ran zero times and passed. A checker that
had been stubbed to do nothing at all would have produced exactly the same
green. That is the module's own subject matter turned on itself -- a result
that reports "no problems" when it has in fact examined nothing.

Pinning the PNG count is not sufficient to close this. It establishes that
*images* exist, not that the *claim-checking logic* works. So the logic is
extracted into :func:`scale_claim_violations` and driven against PNGs built in
a temporary directory: an honest 2x that must be accepted, a lying 2x that must
be rejected, and an orphan 2x with no base. Those fixtures are real PNGs
assembled from the specification -- signature, IHDR, IDAT, IEND, each with its
own CRC -- rather than stubs, so the reader under test is doing genuine work.

The repository-wide assertions are kept as well. They are the ones that would
catch a real recurrence; the seeded ones are what make their silence meaningful.

WHAT THIS MODULE DOES NOT CLAIM
-------------------------------
It does not assert that the brand images are any particular size, and it does
not require a 2x asset to exist. The repository's artwork is 256 everywhere,
including the ``icon.svg`` viewBox, so there is no 512 source to recover -- a
genuine 2x would have to be *created*, which is a design decision and not an
engineering one. Deleting the false claim and asserting that no future one goes
unchecked is the whole of what can be settled here.
"""

import binascii
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# Suffixes whose presence in a filename is a checkable claim, mapped to the
# multiplier they assert against the same name without the suffix.
SCALE_SUFFIXES: dict[str, int] = {
    "@2x": 2,
    "@3x": 3,
    "@4x": 4,
}


def png_dimensions(path: Path) -> tuple[int, int]:
    """Width and height from a PNG's IHDR chunk.

    Read from the header rather than through an imaging library on purpose:
    this module exists because a *claim about* an image went unverified, so it
    should depend on as little interpretation as possible. IHDR is the first
    chunk by specification, at a fixed offset, and the type field is asserted
    rather than assumed -- a reader that silently unpacked four bytes from a
    non-PNG would return a confident wrong number, which is the failure this
    module is about.
    """
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    if data[12:16] != b"IHDR":
        raise ValueError(f"{path} has no IHDR where the spec requires one")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def repository_pngs() -> list[Path]:
    """Every tracked PNG, discovered rather than listed.

    The defect was a file nobody was looking at, so a hand-written list would
    share the blind spot with the thing it is meant to catch.
    """
    return sorted(
        path
        for path in REPO_ROOT.rglob("*.png")
        if ".git" not in path.parts and "__pycache__" not in path.parts
    )


class ScaleClaimViolation(NamedTuple):
    """One falsified filename claim.

    ``kind`` is carried so callers can assert on a specific failure mode rather
    than on a bare count. A test that only knew "something was wrong" would be
    a weaker report than the defect deserves.
    """

    path: str
    kind: str  # "missing-base" | "wrong-dimensions" | "byte-identical"
    message: str


def scale_claim_violations(paths: list[Path]) -> list[ScaleClaimViolation]:
    """Every way the given files fail the claims their names make.

    Extracted from the test bodies so it can be driven against inputs that are
    not this repository's tree. Its assertions were vacuous while no ``@2x``
    file existed here, and a function that can only ever be called with an
    empty list cannot be shown to work.

    A suffixed file whose base is absent counts as a violation rather than a
    skip: it makes a comparative claim with nothing to compare against, and
    skipping would be wrong in the direction that hides defects.
    """
    violations: list[ScaleClaimViolation] = []
    for path in paths:
        for suffix, factor in SCALE_SUFFIXES.items():
            if suffix not in path.stem:
                continue
            base = path.with_name(path.stem.replace(suffix, "") + path.suffix)
            if not base.exists():
                violations.append(
                    ScaleClaimViolation(
                        path.name,
                        "missing-base",
                        f"{path.name} claims {factor}x but {base.name} does not "
                        "exist, so the claim cannot be checked against anything",
                    )
                )
                continue

            base_w, base_h = png_dimensions(base)
            got_w, got_h = png_dimensions(path)
            if (got_w, got_h) != (base_w * factor, base_h * factor):
                violations.append(
                    ScaleClaimViolation(
                        path.name,
                        "wrong-dimensions",
                        f"{path.name} is {got_w}x{got_h}; {suffix} asserts "
                        f"{base_w * factor}x{base_h * factor}. A consumer "
                        "honouring the suffix renders this into a larger slot "
                        "and gets a blurrier result than the 1x would give.",
                    )
                )

            if hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(
                base.read_bytes()
            ).hexdigest():
                violations.append(
                    ScaleClaimViolation(
                        path.name,
                        "byte-identical",
                        f"{path.name} is a byte-for-byte copy of {base.name}",
                    )
                )
    return violations


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    """One length-type-payload-CRC chunk, per the PNG specification."""
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def write_png(path: Path, width: int, height: int, fill: int = 0) -> Path:
    """Assemble a real, valid greyscale PNG of the requested dimensions.

    Built from the specification rather than mocked, because the reader under
    test parses real bytes. ``fill`` lets two images of identical dimensions be
    given different content, which is what separates the honest-2x fixture from
    the byte-identical one.
    """
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    raw = b"".join(b"\x00" + bytes([fill]) * width for _ in range(height))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    return path


class ScaleSuffixClaims(unittest.TestCase):
    """A scale suffix must be true of the pixels."""

    def test_discovery_finds_pngs(self):
        """Control: the walk is not empty.

        Every assertion below quantifies over this list. An empty list satisfies
        all of them for the same reason a clean repository does -- a vacuous
        green and a real green are the same observation, so pin the floor.
        """
        found = repository_pngs()
        self.assertGreaterEqual(len(found), 5, f"only found {found}")

    def test_the_reader_reports_real_dimensions(self):
        """Must-find control: the reader distinguishes two known-different sizes.

        Without this, a reader stuck on one answer -- or one that returned the
        same number for everything -- would satisfy the scale assertions below
        by making every comparison trivially consistent.
        """
        world_map = REPO_ROOT / "custom_components" / "nasa_astronomy" / "world-map.png"
        icon = REPO_ROOT / "custom_components" / "nasa_astronomy" / "icon.png"
        self.assertEqual(png_dimensions(icon), (256, 256))
        self.assertEqual(png_dimensions(world_map), (2000, 959))

    def test_the_reader_rejects_a_non_png(self):
        """Must-find control, inverted: a bad input raises instead of guessing."""
        with self.assertRaises(ValueError):
            png_dimensions(REPO_ROOT / "hacs.json")

    def test_every_scale_suffix_is_true_of_the_pixels(self):
        """The load-bearing assertion, applied to this repository.

        Delegates to :func:`scale_claim_violations` so that the same logic
        asserted here is the logic proven correct against seeded fixtures in
        :class:`SeededScaleClaims`. On its own this assertion is currently
        vacuous -- no ``@2x`` file exists to quantify over -- and that is
        precisely why the checker is not left inline where nothing can reach it.
        """
        offending = [
            violation
            for violation in scale_claim_violations(repository_pngs())
            if violation.kind in {"missing-base", "wrong-dimensions"}
        ]
        self.assertEqual(
            offending, [], "\n".join(v.message for v in offending)
        )

    def test_a_scale_suffix_is_never_byte_identical_to_its_base(self):
        """The specific shape the defect took, pinned separately.

        Implied by the dimension check, but asserted in its own right because
        byte-identity is *why* it survived: every casual check -- the file
        exists, it opens, it looks correct -- passes on a duplicate. Naming it
        makes a recurrence say what it is rather than only reporting a size.
        """
        offending = [
            violation
            for violation in scale_claim_violations(repository_pngs())
            if violation.kind == "byte-identical"
        ]
        self.assertEqual(
            offending, [], "\n".join(v.message for v in offending)
        )


class SeededScaleClaims(unittest.TestCase):
    """Drive the checker against files built to be right and wrong on purpose.

    The repository-wide assertions above cannot currently fail, because the
    files that would fail them were deleted. These can, and they are the reason
    the green above means anything: if :func:`scale_claim_violations` were
    stubbed to return nothing, every test here would fail immediately.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_builder_produces_readable_pngs(self):
        """Must-find control for the fixtures themselves.

        Every case below depends on ``write_png`` emitting something the reader
        can parse. A builder that produced malformed bytes would make the
        rejection cases pass for entirely the wrong reason.
        """
        made = write_png(self.tmp_path / "probe.png", 512, 256)
        self.assertEqual(png_dimensions(made), (512, 256))

    def test_an_honest_2x_is_accepted(self):
        """A true 2x must produce no violations.

        The direction that matters most: a checker which simply reported
        everything as broken would satisfy both failure cases below while being
        useless. This is what stops that.
        """
        write_png(self.tmp_path / "icon.png", 256, 256, fill=0)
        asset = write_png(self.tmp_path / "icon@2x.png", 512, 512, fill=255)
        self.assertEqual(scale_claim_violations([asset]), [])

    def test_a_lying_2x_is_rejected(self):
        """The original defect, reconstructed: 256 pixels behind a 2x name."""
        write_png(self.tmp_path / "icon.png", 256, 256, fill=0)
        asset = write_png(self.tmp_path / "icon@2x.png", 256, 256, fill=255)
        kinds = [v.kind for v in scale_claim_violations([asset])]
        self.assertIn("wrong-dimensions", kinds)

    def test_a_byte_identical_2x_is_rejected_as_such(self):
        """The defect in the exact form it took here: a copy, not merely small.

        Asserts both kinds fire, because a duplicate is simultaneously the
        wrong size and the same bytes, and the report should say both.
        """
        write_png(self.tmp_path / "icon.png", 256, 256, fill=7)
        asset = write_png(self.tmp_path / "icon@2x.png", 256, 256, fill=7)
        kinds = [v.kind for v in scale_claim_violations([asset])]
        self.assertIn("byte-identical", kinds)
        self.assertIn("wrong-dimensions", kinds)

    def test_a_2x_with_no_base_is_rejected(self):
        """An unfalsifiable claim is a violation, not a skip."""
        asset = write_png(self.tmp_path / "icon@2x.png", 512, 512)
        kinds = [v.kind for v in scale_claim_violations([asset])]
        self.assertEqual(kinds, ["missing-base"])

    def test_every_declared_suffix_is_actually_enforced(self):
        """The table is data, so prove each row is wired to the check.

        ``SCALE_SUFFIXES`` gaining an entry that nothing enforces would be the
        same defect one level up: a declaration that reads as a guarantee while
        checking nothing.
        """
        for suffix, factor in SCALE_SUFFIXES.items():
            with self.subTest(suffix=suffix):
                base_dir = self.tmp_path / suffix.strip("@")
                base_dir.mkdir()
                write_png(base_dir / "icon.png", 64, 64, fill=0)
                honest = write_png(
                    base_dir / f"icon{suffix}.png", 64 * factor, 64 * factor, fill=1
                )
                self.assertEqual(scale_claim_violations([honest]), [])
                liar = write_png(base_dir / f"logo{suffix}.png", 64, 64, fill=1)
                write_png(base_dir / "logo.png", 64, 64, fill=0)
                self.assertIn(
                    "wrong-dimensions",
                    [v.kind for v in scale_claim_violations([liar])],
                )


def duplicate_png_groups(paths: list[Path] | None = None) -> dict[str, list[str]]:
    """Content digests carried by more than one file, mapped to those files.

    Takes ``paths`` so it can be driven against seeded inputs. A grouping
    function that can only ever be called with this repository's tree cannot be
    shown to group anything -- and if it silently returned ``{}`` the assertion
    below would still need to fail, which is why that assertion pins an exact
    shape rather than an upper bound.
    """
    if paths is None:
        paths = repository_pngs()
    digests: dict[str, list[str]] = {}
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            name = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            name = path.name
        digests.setdefault(digest, []).append(name)
    return {
        digest: sorted(names)
        for digest, names in digests.items()
        if len(names) > 1
    }


class DuplicateBrandAssets(unittest.TestCase):
    """Exactly one set of byte-identical PNGs is sanctioned here.

    The brand icon is carried at six paths. That is deliberate: deleting the
    copies was declined in #35 and #40 -- "the identical brand files are
    intentional" -- and again when #55 was closed. HACS additionally requires a
    ``brand`` directory containing ``icon.png`` for an integration repository to
    validate, so at least one of those copies is load-bearing to CI.

    The previous form of this test asserted only that no group exceeded six.
    That bound was set by the brand icon and therefore guarded nothing else: a
    546 KB ``world-map.png`` was duplicated into ``www/`` for months, and a
    third copy of it could have been added without turning this red. An upper
    bound derived from the largest known offender cannot detect a smaller new
    one.

    So this pins the shape instead -- one sanctioned group, of a known size.
    A new duplicate group is a new decision, and it should have to be made
    deliberately rather than inherited from whichever file happened to be
    biggest.
    """

    SANCTIONED_GROUP_SIZE = 6

    def test_the_grouper_actually_groups(self):
        """Must-find control: seeded identical files are detected as a group.

        Without this, a grouper that returned ``{}`` for everything would be
        caught by the assertion below only by accident of its exact wording.
        Pinned directly so the reason is legible.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_png(root / "a.png", 8, 8, fill=1)
            write_png(root / "b.png", 8, 8, fill=1)
            write_png(root / "c.png", 8, 8, fill=2)
            groups = duplicate_png_groups(
                [root / "a.png", root / "b.png", root / "c.png"]
            )
            self.assertEqual(len(groups), 1)
            self.assertEqual(next(iter(groups.values())), ["a.png", "b.png"])

    def test_distinct_files_produce_no_group(self):
        """Must-find control, inverted: it does not invent duplicates."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_png(root / "a.png", 8, 8, fill=1)
            write_png(root / "b.png", 8, 8, fill=2)
            self.assertEqual(
                duplicate_png_groups([root / "a.png", root / "b.png"]), {}
            )

    def test_only_the_sanctioned_brand_group_is_duplicated(self):
        """The load-bearing assertion: one group, of the size we agreed to."""
        groups = duplicate_png_groups()
        self.assertEqual(
            len(groups),
            1,
            "expected exactly one sanctioned group of byte-identical PNGs "
            f"(the brand icon); found {len(groups)}: {groups!r}",
        )
        only = next(iter(groups.values()))
        self.assertEqual(
            len(only),
            self.SANCTIONED_GROUP_SIZE,
            f"the sanctioned brand group is now {len(only)} files: {only!r}",
        )


if __name__ == "__main__":
    unittest.main()
