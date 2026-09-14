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

WHAT THIS MODULE DOES NOT CLAIM
-------------------------------
It does not assert that the brand images are any particular size, and it does
not require a 2x asset to exist. The repository's artwork is 256 everywhere,
including the ``icon.svg`` viewBox, so there is no 512 source to recover -- a
genuine 2x would have to be *created*, which is a design decision and not an
engineering one. Deleting the false claim and asserting that no future one goes
unchecked is the whole of what can be settled here.

THE DE-DUPLICATION, AND WHAT IT DID TO THE CONTROLS
---------------------------------------------------
``DuplicateBrandAssets`` below used to record six byte-identical copies of one
32,483-byte file as a bound that must not *grow*, explicitly declining to say
which locations were needed on the grounds that it was a packaging decision.
That decision has since been made and taken: the only path Home Assistant's
brand convention reads is ``custom_components/<domain>/brand/``, so the copies
at the repository root and loose in the package directory were removed and the
``brand/`` directory keeps ``icon.png`` alone.

That removal broke two controls in this module, and the way it broke them is
worth stating because it is the failure mode the controls exist to announce:

* ``test_discovery_finds_pngs`` pinned a floor of five PNGs. After the dedupe
  three remain, so the floor failed -- correctly. Every scale-suffix assertion
  here quantifies over that walk, and a walk returning too little makes them
  pass vacuously. The floor is now derived from a *named* set rather than a
  magic number, so it says which files must be found instead of how many.
* ``test_the_reader_reports_real_dimensions`` used the now-deleted
  ``custom_components/nasa_astronomy/icon.png`` as its known-256 fixture. It is
  re-pointed at the surviving canonical icon. The control is unchanged in kind:
  it still proves the reader distinguishes two known-different sizes, which is
  the only property it was ever asserting.

Neither was weakened to get green. The floor got stricter, and a seeded fixture
was added below because the scale-suffix assertions are vacuous on this
repository in *either* state -- there are no ``@2x`` files left to check, and
there were none on ``main`` before this change either. A test that cannot fail
is the defect this project keeps removing, so the logic those assertions run is
now exercised against constructed inputs that must make it fire.
"""

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Suffixes whose presence in a filename is a checkable claim, mapped to the
# multiplier they assert against the same name without the suffix.
SCALE_SUFFIXES: dict[str, int] = {
    "@2x": 2,
    "@3x": 3,
    "@4x": 4,
}

# The PNGs this repository is known to carry, named rather than counted.
#
# A bare `>= N` floor answers "did the walk return enough things", which is the
# right question asked the wrong way: it cannot tell a walk that lost the brand
# icon from one that gained an unrelated screenshot. Naming them means the
# control fails on the change that matters -- a canonical asset going missing --
# and stays quiet on one that does not.
CANONICAL_PNGS: frozenset[str] = frozenset(
    {
        "custom_components/nasa_astronomy/brand/icon.png",
        "custom_components/nasa_astronomy/world-map.png",
        "www/community/astronomy-cards/world-map.png",
    }
)


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


def scale_claim_violations(paths: list[Path]) -> list[str]:
    """Every way the files in ``paths`` break a scale claim their name makes.

    Extracted from the test body so the seeded fixtures below can run *this*
    function rather than a re-implementation of it. A fixture that exercises a
    copy of the logic proves only that the copy works, which is how a check can
    be thoroughly tested and still not be wired to anything.
    """
    problems = []
    for path in paths:
        for suffix, factor in SCALE_SUFFIXES.items():
            if suffix not in path.stem:
                continue
            base = path.with_name(path.stem.replace(suffix, "") + path.suffix)
            if not base.exists():
                problems.append(
                    f"{path.name} claims {factor}x but {base.name} does not "
                    "exist, so the claim cannot be checked against anything"
                )
                continue
            base_w, base_h = png_dimensions(base)
            got_w, got_h = png_dimensions(path)
            if (got_w, got_h) != (base_w * factor, base_h * factor):
                problems.append(
                    f"{path.name} is {got_w}x{got_h}; {suffix} asserts "
                    f"{base_w * factor}x{base_h * factor}. A consumer honouring "
                    "the suffix renders this into a larger slot and gets a "
                    "blurrier result than the 1x would give."
                )
            if hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(
                base.read_bytes()
            ).hexdigest():
                problems.append(f"{path.name} is a byte-for-byte copy of {base.name}")
    return problems


def write_png(path: Path, width: int, height: int, filler: bytes = b"") -> Path:
    """A structurally valid PNG header of a stated size, for fixtures.

    Only the signature and IHDR need to be real: ``png_dimensions`` reads
    nothing else, and a fixture that carried a full encoder would be testing
    the encoder. ``filler`` exists so two images of identical dimensions can be
    made to differ in bytes, which is what separates the size assertion from
    the byte-identity one.
    """
    header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
    header += struct.pack(">II", width, height)
    header += b"\x08\x06\x00\x00\x00"
    path.write_bytes(header + filler)
    return path


class ScaleSuffixClaims(unittest.TestCase):
    """A scale suffix must be true of the pixels."""

    def test_discovery_finds_pngs(self):
        """Control: the walk finds every asset the repository is known to carry.

        Every assertion below quantifies over this list. An empty or truncated
        list satisfies all of them for the same reason a clean repository does
        -- a vacuous green and a real green are the same observation -- so the
        floor is pinned to a named set rather than a count.
        """
        found = repository_pngs()
        relative = {p.relative_to(REPO_ROOT).as_posix() for p in found}
        missing = sorted(CANONICAL_PNGS - relative)
        self.assertFalse(
            missing,
            f"the walk did not find {missing}; it returned {sorted(relative)}",
        )
        self.assertGreaterEqual(
            len(found),
            len(CANONICAL_PNGS),
            f"only found {sorted(relative)}",
        )

    def test_the_reader_reports_real_dimensions(self):
        """Must-find control: the reader distinguishes two known-different sizes.

        Without this, a reader stuck on one answer -- or one that returned the
        same number for everything -- would satisfy the scale assertions below
        by making every comparison trivially consistent.

        The 256 fixture is the canonical brand icon. It was previously the copy
        at ``custom_components/nasa_astronomy/icon.png``, which was one of six
        byte-identical duplicates and has been removed; the property under test
        is unchanged, because any two assets of known and different size serve.
        """
        world_map = REPO_ROOT / "custom_components" / "nasa_astronomy" / "world-map.png"
        icon = REPO_ROOT / "custom_components" / "nasa_astronomy" / "brand" / "icon.png"
        self.assertEqual(png_dimensions(icon), (256, 256))
        self.assertEqual(png_dimensions(world_map), (2000, 959))

    def test_the_reader_rejects_a_non_png(self):
        """Must-find control, inverted: a bad input raises instead of guessing."""
        with self.assertRaises(ValueError):
            png_dimensions(REPO_ROOT / "hacs.json")

    def test_every_scale_suffix_is_true_of_the_pixels(self):
        """The load-bearing assertion.

        A ``@2x`` file must be twice the dimensions of its base, and must not be
        a byte-for-byte copy of it. Skipping when the base is absent would be
        wrong in the direction that hides defects, so a suffixed file with no
        base is itself a failure: it makes a comparative claim with nothing to
        compare against.

        This is vacuous on the repository as it stands -- no ``@2x`` file
        survives -- which is why the fixtures below exist. It stays here to fail
        the moment one is reintroduced.
        """
        violations = scale_claim_violations(repository_pngs())
        self.assertFalse(violations, "\n    ".join(violations))


class SeededScaleClaimTests(unittest.TestCase):
    """The scale check, run against inputs that must make it fire.

    ``test_every_scale_suffix_is_true_of_the_pixels`` quantifies over a set that
    is currently empty of ``@2x`` files, so on its own it is a green that means
    nothing. These construct the three shapes the defect can take and assert the
    same function reports each one, so the logic guarding the repository is
    known to work rather than merely known to be silent.
    """

    def test_an_honest_2x_is_accepted(self):
        """Non-vacuity in the other direction.

        Without this, a checker that flagged everything would pass all three
        tests below and still be useless -- it would block a correct asset.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_png(root / "icon.png", 256, 256)
            two_x = write_png(root / "icon@2x.png", 512, 512, filler=b"different")
            self.assertEqual([], scale_claim_violations([two_x]))

    def test_a_2x_that_is_not_double_is_reported(self):
        """The dimension lie: the exact shape of the original defect."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_png(root / "icon.png", 256, 256)
            two_x = write_png(root / "icon@2x.png", 256, 256, filler=b"different")
            violations = scale_claim_violations([two_x])
            self.assertTrue(violations, "a 256x256 @2x of a 256x256 base passed")
            self.assertIn("256x256", violations[0])

    def test_a_2x_byte_identical_to_its_base_is_reported(self):
        """Byte-identity, pinned separately because it is *why* it survived.

        Every casual check -- the file exists, it opens, it looks correct --
        passes on a duplicate.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_png(root / "icon.png", 256, 256)
            two_x = write_png(root / "icon@2x.png", 256, 256)
            violations = scale_claim_violations([two_x])
            self.assertTrue(
                any("byte-for-byte" in v for v in violations),
                f"byte-identity went unreported: {violations}",
            )

    def test_a_2x_with_no_base_is_reported(self):
        """A comparative claim with nothing to compare against."""
        with tempfile.TemporaryDirectory() as tmp:
            two_x = write_png(Path(tmp) / "icon@2x.png", 512, 512)
            violations = scale_claim_violations([two_x])
            self.assertTrue(
                any("does not exist" in v for v in violations),
                f"an orphaned @2x went unreported: {violations}",
            )


class DuplicateBrandAssets(unittest.TestCase):
    """The duplication is now bounded by what is actually needed.

    This used to permit six byte-identical copies of one 32,483-byte file,
    declining to pick the necessary locations because that was a packaging
    decision. It has been made: Home Assistant reads brand images from
    ``custom_components/<domain>/brand/``, so one copy of the icon lives there
    and the rest were removed.

    The bound is therefore tightened to the duplication that remains and is
    deliberate -- ``world-map.png`` is mirrored into ``www/`` -- so that the
    copies which were just removed cannot quietly return. A bound left at six
    after a dedupe to one is not a bound; it is permission.
    """

    KNOWN_DUPLICATE_COUNT = 2

    def test_identical_brand_copies_do_not_multiply(self):
        digests: dict[str, list[str]] = {}
        for path in repository_pngs():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            digests.setdefault(digest, []).append(path.relative_to(REPO_ROOT).as_posix())
        worst = max((len(paths) for paths in digests.values()), default=0)
        self.assertLessEqual(
            worst,
            self.KNOWN_DUPLICATE_COUNT,
            "the number of byte-identical PNG copies has grown: "
            + repr({d[:8]: p for d, p in digests.items() if len(p) > 1}),
        )

    def test_the_removed_duplicates_stay_removed(self):
        """Named, because a bound on the count would not notice these return.

        Five of the six copies were the same bytes as the icon, so restoring any
        one of them raises the worst-group count above the bound -- but only
        while the bound is where it is. Naming the paths makes the recurrence
        report what it is rather than only that a number moved.
        """
        removed = [
            "icon.png",
            "logo.png",
            "custom_components/nasa_astronomy/icon.png",
            "custom_components/nasa_astronomy/logo.png",
            "custom_components/nasa_astronomy/brand/logo.png",
            "custom_components/nasa_astronomy/brand/icon@2x.png",
            "custom_components/nasa_astronomy/brand/logo@2x.png",
        ]
        present = [p for p in removed if (REPO_ROOT / p).exists()]
        self.assertFalse(
            present,
            "these were removed as duplicates or as false scale claims and "
            "must not come back:\n    " + "\n    ".join(present),
        )


if __name__ == "__main__":
    unittest.main()
