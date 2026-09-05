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
"""

import hashlib
import struct
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
        """The load-bearing assertion.

        A ``@2x`` file must be twice the dimensions of its base. Skipping when
        the base is absent would be wrong in the direction that hides defects,
        so a suffixed file with no base is itself a failure: it makes a
        comparative claim with nothing to compare against.
        """
        for path in repository_pngs():
            for suffix, factor in SCALE_SUFFIXES.items():
                if suffix not in path.stem:
                    continue
                base = path.with_name(path.stem.replace(suffix, "") + path.suffix)
                with self.subTest(asset=path.name):
                    self.assertTrue(
                        base.exists(),
                        f"{path.name} claims {factor}x but {base.name} does not exist, "
                        "so the claim cannot be checked against anything",
                    )
                    base_w, base_h = png_dimensions(base)
                    got_w, got_h = png_dimensions(path)
                    self.assertEqual(
                        (got_w, got_h),
                        (base_w * factor, base_h * factor),
                        f"{path.name} is {got_w}x{got_h}; {suffix} asserts "
                        f"{base_w * factor}x{base_h * factor}. A consumer "
                        "honouring the suffix renders this into a larger slot "
                        "and gets a blurrier result than the 1x would give.",
                    )

    def test_a_scale_suffix_is_never_byte_identical_to_its_base(self):
        """The specific shape the defect took, pinned separately.

        Implied by the dimension check, but asserted in its own right because
        byte-identity is *why* it survived: every casual check -- the file
        exists, it opens, it looks correct -- passes on a duplicate. Naming it
        makes a recurrence say what it is rather than only reporting a size.
        """
        for path in repository_pngs():
            for suffix in SCALE_SUFFIXES:
                if suffix not in path.stem:
                    continue
                base = path.with_name(path.stem.replace(suffix, "") + path.suffix)
                if not base.exists():
                    continue
                with self.subTest(asset=path.name):
                    self.assertNotEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        hashlib.sha256(base.read_bytes()).hexdigest(),
                        f"{path.name} is a byte-for-byte copy of {base.name}",
                    )


class DuplicateBrandAssets(unittest.TestCase):
    """Record the duplication, without asserting a particular layout.

    Eight identical copies of one 32,483-byte file were carried in six
    directories. De-duplicating fully means deciding which locations Home
    Assistant, HACS and the README each need, and that is a packaging decision
    rather than a measurable defect -- so this asserts the bound that *is*
    settled: the count must not grow.
    """

    KNOWN_DUPLICATE_COUNT = 6

    def test_identical_brand_copies_do_not_multiply(self):
        digests: dict[str, list[str]] = {}
        for path in repository_pngs():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            digests.setdefault(digest, []).append(
                path.relative_to(REPO_ROOT).as_posix()
            )
        worst = max((len(paths) for paths in digests.values()), default=0)
        self.assertLessEqual(
            worst,
            self.KNOWN_DUPLICATE_COUNT,
            "the number of byte-identical PNG copies has grown: "
            + repr({d[:8]: p for d, p in digests.items() if len(p) > 1}),
        )


if __name__ == "__main__":
    unittest.main()
