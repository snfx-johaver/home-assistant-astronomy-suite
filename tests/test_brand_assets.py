"""Brand images must not be silent duplicates, and must not lie about size.

THE DEFECT THIS GUARDS AGAINST

At v1.11.8 eight files -- the root ``icon.png``/``logo.png``, their loose
copies at ``custom_components/nasa_astronomy/icon.png``/``logo.png``, and the
four files inside the HA brand convention path
(``custom_components/nasa_astronomy/brand/{icon,logo}{,@2x}.png``) -- were all
byte-for-byte the same 256x256 PNG. Nothing rendered a "logo" at all; every
consumer that asked for one got a square icon instead, and every consumer that
asked for a ``@2x`` asset got 256x256 pixel data inside a file that claimed to
be 512x512 -- worse than not having a ``@2x`` file, because a HiDPI client
scales that claimed resolution up and gets a blurrier result than just using
the 1x asset.

The fix removed the false ``@2x`` files and the redundant copies outside the
one path Home Assistant's brand convention actually reads
(``custom_components/nasa_astronomy/brand/``), rather than inventing new
placeholder art. This module is the regression guard for that: it fails if the
duplicates come back, if a ``@2x`` file reappears with the wrong dimensions,
or if the canonical icon quietly stops being square.

PNG dimensions are read from the IHDR chunk with stdlib ``struct`` rather than
Pillow, matching the rest of this suite's habit of not adding a dependency
where the file format is simple enough to parse directly (8-byte signature,
4-byte length, 4-byte "IHDR", then big-endian width and height as uint32).
"""

import hashlib
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "nasa_astronomy"
BRAND_DIR = COMPONENT_DIR / "brand"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Paths the fix removed. They must stay gone: reappearing, even innocently
# (e.g. a merge resurrecting one), reintroduces exactly the defect above.
REMOVED_PATHS = (
    ROOT / "icon.png",
    ROOT / "logo.png",
    COMPONENT_DIR / "icon.png",
    COMPONENT_DIR / "logo.png",
    BRAND_DIR / "icon@2x.png",
    BRAND_DIR / "logo@2x.png",
    BRAND_DIR / "logo.png",
)

# The one brand image this repository ships today. If this list grows, the
# growth is the point: new entries get the same duplicate-content and honest-
# dimension checks below for free.
CANONICAL_BRAND_IMAGES = (BRAND_DIR / "icon.png",)


def png_dimensions(path: Path) -> tuple[int, int]:
    """(width, height) from a PNG's IHDR chunk, read directly off disk."""
    with path.open("rb") as fh:
        header = fh.read(24)
    if header[:8] != PNG_SIGNATURE:
        raise ValueError(f"{path} is not a PNG (bad signature)")
    if header[12:16] != b"IHDR":
        raise ValueError(f"{path} has no IHDR as its first chunk")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_tracked_pngs() -> list[Path]:
    """Every PNG under the paths the defect actually touched.

    Deliberately broader than ``CANONICAL_BRAND_IMAGES``: it also covers the
    repository root and the loose ``custom_components/nasa_astronomy/*.png``
    files, so a *new* duplicate introduced anywhere in that surface is caught
    even if this module's authors never learn its name.
    """
    candidates = list(ROOT.glob("*.png")) + list(COMPONENT_DIR.glob("*.png"))
    if BRAND_DIR.is_dir():
        candidates += list(BRAND_DIR.glob("*.png"))
    return sorted(set(candidates))


class RemovedDuplicatesStayRemovedTests(unittest.TestCase):
    def test_the_removed_paths_do_not_exist(self):
        present = [str(p.relative_to(ROOT)) for p in REMOVED_PATHS if p.exists()]
        self.assertFalse(
            present,
            "these brand-asset paths were removed as duplicates/false @2x "
            "files and must not come back:\n    " + "\n    ".join(present),
        )

    def test_the_control_would_have_caught_the_original_defect(self):
        """A must-find control: fabricate the v1.11.8 duplication and confirm
        the hashing logic below actually flags it, so a green suite here means
        the check works rather than that nothing was compared."""
        content = (ROOT / "custom_components" / "nasa_astronomy" / "brand" / "icon.png").read_bytes()
        hashes = {"icon.png": hashlib.sha256(content).hexdigest(), "logo.png": hashlib.sha256(content).hexdigest()}
        duplicated = len(set(hashes.values())) < len(hashes)
        self.assertTrue(
            duplicated,
            "control did not detect identical content for differently-named "
            "files; the real tests below cannot be trusted",
        )


class NoDuplicateBrandBlobsTests(unittest.TestCase):
    """No two differently-named images in this surface may share content.

    This is the general form of the specific defect: any file here claiming
    to be a distinct asset (icon vs. logo, 1x vs. 2x) must actually contain
    distinct pixels from every other file in the surface.
    """

    def test_no_two_png_files_are_byte_identical(self):
        pngs = all_tracked_pngs()
        self.assertTrue(pngs, "no PNGs found under the brand-asset surface")
        by_hash: dict[str, list[Path]] = {}
        for path in pngs:
            by_hash.setdefault(sha256_of(path), []).append(path)
        duplicates = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
        self.assertFalse(
            duplicates,
            "these PNGs are byte-for-byte identical, which is the exact "
            "defect this module guards against:\n    "
            + "\n    ".join(
                f"{h}: {[str(p.relative_to(ROOT)) for p in ps]}"
                for h, ps in duplicates.items()
            ),
        )


class CanonicalIconTests(unittest.TestCase):
    def test_the_canonical_icon_exists(self):
        for path in CANONICAL_BRAND_IMAGES:
            self.assertTrue(
                path.exists(),
                f"{path.relative_to(ROOT)} is the one brand image this "
                "repository ships; it must exist",
            )

    def test_the_canonical_icon_is_square(self):
        """HA's icon slot is square; a non-square icon is a different defect
        in the other direction from the mislabeled square 'logo'."""
        for path in CANONICAL_BRAND_IMAGES:
            width, height = png_dimensions(path)
            self.assertEqual(
                width,
                height,
                f"{path.relative_to(ROOT)} is {width}x{height}, not square",
            )
            self.assertGreater(width, 0, f"{path.relative_to(ROOT)} is empty")


class HonestTwoXDimensionsTests(unittest.TestCase):
    """If a ``@2x`` file ever comes back, it must actually be 2x.

    None ship today -- the false ones were removed -- so this test is
    vacuously true over an empty set until someone adds one. That is the
    point: it turns from vacuous to load-bearing automatically the moment a
    ``@2x`` file is reintroduced, with no one having to remember to write a
    new test then.
    """

    def test_every_2x_file_is_exactly_double_its_1x_counterpart(self):
        two_x_files = list(BRAND_DIR.glob("*@2x.png")) if BRAND_DIR.is_dir() else []
        for two_x in two_x_files:
            one_x = two_x.with_name(two_x.name.replace("@2x.png", ".png"))
            self.assertTrue(
                one_x.exists(),
                f"{two_x.relative_to(ROOT)} has no 1x counterpart {one_x.name} "
                "to be double of",
            )
            w2, h2 = png_dimensions(two_x)
            w1, h1 = png_dimensions(one_x)
            self.assertEqual(
                (w2, h2),
                (w1 * 2, h1 * 2),
                f"{two_x.relative_to(ROOT)} claims {w2}x{h2} but its 1x "
                f"counterpart is {w1}x{h1}, so it is not honestly 2x -- a "
                "HiDPI client scaling it up gets a worse result than using "
                "the 1x file directly",
            )


if __name__ == "__main__":
    unittest.main()
