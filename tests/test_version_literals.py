"""Every version-shaped literal in the repository must be accounted for.

WHY THIS EXISTS, AND WHY IT IS NOT A GLOB
-----------------------------------------
Two bundles have now shipped a stale version for fourteen releases apiece.
``deepsky-cards.js`` sat at ``1.0.0`` because it was absent from a hand-written
list in the release script. The fix replaced that list with a
``glob("*-cards.js")`` -- an improvement, because it discovered the bundle
nobody had registered.

It was still wrong, and ``index.ts`` proves it: it announced ``v1.0.0`` to the
browser console from the day it was written, and a glob for ``*-cards.js``
cannot see a file called ``index.ts``.

The lesson is *not* "don't declare the universe" -- every test declares one.
It is that the glob **failed closed**: a file outside the pattern was silently
skipped, and silence is indistinguishable from success. This module declares
its universe at the widest point available (every tracked file, every
``\\d+\\.\\d+\\.\\d+``) and **fails open**: a literal nobody has classified
fails the suite and names itself. Adding a file that carries a version now
forces a decision instead of inheriting one.

CLASSIFICATION
--------------
Every version-shaped literal is one of:

* ``RELEASE_MAINTAINED`` -- a claim about *this product's* current version. It
  must equal the release version, and the release script must actually write
  it. Both halves matter: ``index.ts`` would have satisfied the first for
  exactly as long as it took the next release to fire.
* ``NOT_A_PRODUCT_VERSION`` -- a historical record, prose, or somebody else's
  version. Frozen by design, with the reason recorded next to it.
* Dependency *ranges* (``^1.2.3``, ``~1.2.3``, ``>=1.2.3``) anywhere -- a
  constraint on another package, never a claim about us.

NOTE ON ORDERING
----------------
``INTEGRATION_VERSION`` resolves once at import (see
``test_device_info_version.py``), but this module reads ``manifest.json``
directly on each call, so it is immune to that ordering hazard.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "custom_components" / "nasa_astronomy" / "manifest.json"

sys.path.insert(0, str(ROOT / "scripts"))

# Deliberately over-broad. Narrowing this is how the previous two defects
# survived; anything it over-reports gets classified once, by hand, with a
# reason attached.
#
# The lookarounds exclude only digits and dots, so that `1.2.3.4` does not
# register as a version but `v1.11.5` does. An earlier draft excluded all word
# characters, which silently blinded the sweep to every `v`-prefixed banner --
# including the `v1.0.0` in index.ts that prompted this module. See
# test_the_sweep_finds_every_literal_the_release_script_rewrites, which is the
# control that catches exactly that class of mistake.
VERSION_SHAPED = re.compile(r"(?<![\d.])\d+\.\d+\.\d+(?![\d.])")

# A caret/tilde/comparator in front of the literal makes it a constraint on
# somebody else's package rather than a claim about this one.
DEPENDENCY_RANGE = re.compile(r"[\^~]|>=?|<=?")

# Files whose version-shaped literals claim to be *this product's* version.
# Every literal in these must equal the release version AND be written by the
# release script -- see the two tests below, which check those separately.
RELEASE_MAINTAINED = {
    "version.json",
    "custom_components/nasa_astronomy/manifest.json",
    "www/community/astronomy-cards/package.json",
    "custom_components/nasa_astronomy/astronomy-cards.js",
    "www/community/astronomy-cards/astronomy-cards.js",
    "custom_components/nasa_astronomy/deepsky-cards.js",
    "www/community/astronomy-cards/deepsky-cards.js",
    "www/community/astronomy-cards/index.ts",
}

# Literals that are not claims about the current release. The reason is the
# point of the entry: "we decided not to care" is how index.ts reached 1.0.0,
# so an entry here has to say what the number actually is.
NOT_A_PRODUCT_VERSION = {
    "README.md": "changelog headings recording past releases; frozen by design",
    "hacs.json": "minimum supported Home Assistant version, not ours",
    "scripts/bump_version.py": "comments describing the 1.0.0 drift incident",
    "tests/cards.test.mjs": "names the release whose defects it regression-tests",
    "tests/test_cards_resource_version.py": "docstring prose describing past drift",
    "tests/test_device_info_version.py": "docstring quoting the original stale values",
    "tests/test_version_literals.py": "this docstring, describing the same incidents",
}

# Build configs are discovered rather than listed, but a glob that finds
# nothing is a check that silently passes -- see test_build_configs_were_found.
BUILD_CONFIG_SUFFIXES = (".config.mjs", ".config.js", ".config.ts")
OUTPUT_FILE = re.compile(r"""file\s*:\s*["']([^"']+)["']""")


def release_version():
    """Read the release version from the manifest on every call.

    Deliberately not imported from ``const.INTEGRATION_VERSION``: that constant
    is the thing under test elsewhere, and reading it here would let a broken
    constant agree with itself.
    """
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return sorted(out)


def version_literals_in(relative_path):
    """Yield ``(lineno, literal, line)`` for every product-version candidate.

    Dependency ranges are excluded here rather than classified per-file,
    because ``^1.2.3`` means the same thing wherever it appears.
    """
    path = ROOT / relative_path
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        for match in VERSION_SHAPED.finditer(line):
            prefix = line[max(0, match.start() - 2):match.start()]
            if DEPENDENCY_RANGE.search(prefix):
                continue
            yield lineno, match.group(0), line.strip()


def files_with_version_literals():
    found = {}
    for name in tracked_files():
        hits = list(version_literals_in(name))
        if hits:
            found[name] = hits
    return found


def paths_the_release_script_writes():
    """Ask the release script itself which files it maintains.

    Runs the planners rather than reading their configuration. Reading
    ``CARD_BUNDLES`` would only confirm that the list agrees with itself, and
    the list is precisely what was wrong both previous times.
    """
    return {path for path, _count in _release_script_plan().items()}


SENTINEL = "9.9.9"


def _release_script_plan():
    """Map each planned path to how many literals the release script rewrites.

    Planning with a sentinel version and counting its occurrences gives a
    per-file literal count derived from the script's own behaviour, with
    nothing hand-listed. That count is what makes the must-find control
    literal-granular instead of file-granular.
    """
    import bump_version

    plan = {}
    for _label, planner in bump_version.PLAN_STEPS:
        for path, content in planner(SENTINEL):
            relative = Path(path).resolve().relative_to(ROOT).as_posix()
            plan[relative] = content.count(SENTINEL)
    return plan


def discovered_build_configs():
    return [
        name
        for name in tracked_files()
        if name.endswith(BUILD_CONFIG_SUFFIXES)
    ]


class VersionLiteralClassificationTests(unittest.TestCase):
    """Nothing carrying a version may go unclassified."""

    def test_the_sweep_finds_every_file_the_release_script_writes(self):
        """Audit the instrument before trusting what it fails to find.

        A sweep that cannot see files the release script demonstrably writes
        has no authority over the files it reports as clean. This is the
        must-find control, kept permanently rather than run once.
        """
        found = set(files_with_version_literals())
        written = paths_the_release_script_writes()
        self.assertTrue(written, "release script reported writing nothing")
        missed = written - found
        self.assertEqual(
            set(),
            missed,
            "the version sweep missed files the release script writes, so it "
            f"cannot be trusted about anything else: {sorted(missed)}",
        )

    def test_the_sweep_finds_every_literal_the_release_script_rewrites(self):
        """The same control at literal granularity, which is where it bites.

        Checking only that the *file* was found is too coarse to detect a
        blind spot inside it. The first draft of this module could not see
        ``v``-prefixed versions; ``astronomy-cards.js`` still appeared in the
        results, because its unprefixed ``const VERSION`` was visible while
        both of its ``Cards v1.11.5`` banners were not. File-granular controls
        cannot catch that. Counts, derived from the script's own output, can.
        """
        plan = _release_script_plan()
        self.assertTrue(plan, "release script reported writing nothing")
        for path, rewritten in sorted(plan.items()):
            with self.subTest(path=path):
                seen = len(list(version_literals_in(path)))
                self.assertGreaterEqual(
                    seen,
                    rewritten,
                    f"the release script rewrites {rewritten} version literals "
                    f"in {path} but the sweep can only see {seen}: the sweep "
                    "has a blind spot and cannot be trusted about any file",
                )

    def test_every_version_literal_is_classified(self):
        """The fail-open property. New literal, no classification, red."""
        classified = RELEASE_MAINTAINED | set(NOT_A_PRODUCT_VERSION)
        unclassified = {
            name: hits
            for name, hits in files_with_version_literals().items()
            if name not in classified
        }
        if unclassified:
            detail = "\n".join(
                f"  {name}:{lineno}  {literal}   {line[:80]}"
                for name, hits in sorted(unclassified.items())
                for lineno, literal, line in hits
            )
            self.fail(
                "version-shaped literals belong to no classification. Add each "
                "file to RELEASE_MAINTAINED (and to the release script) or to "
                f"NOT_A_PRODUCT_VERSION with a reason:\n{detail}"
            )

    def test_classifications_refer_to_files_that_exist(self):
        """A registry that outlives its files rots into decoration."""
        for name in sorted(RELEASE_MAINTAINED | set(NOT_A_PRODUCT_VERSION)):
            with self.subTest(path=name):
                self.assertTrue(
                    (ROOT / name).is_file(), f"{name} is classified but absent"
                )


class ReleaseMaintainedVersionTests(unittest.TestCase):
    """The two halves of "maintained", checked separately."""

    def test_every_release_maintained_literal_equals_the_release_version(self):
        expected = release_version()
        for name in sorted(RELEASE_MAINTAINED):
            for lineno, literal, line in version_literals_in(name):
                with self.subTest(path=name, line=lineno):
                    self.assertEqual(
                        expected,
                        literal,
                        f"{name}:{lineno} claims version {literal} while the "
                        f"release is {expected}   ({line[:70]})",
                    )

    def test_every_release_maintained_file_is_written_by_the_release_script(self):
        """Agreeing with the release today is not the same as tracking it.

        This is the assertion that would have caught both previous defects at
        the moment they were introduced: ``deepsky-cards.js`` and ``index.ts``
        each agreed with the release on the day they were written, and drifted
        the first time one was cut.
        """
        written = paths_the_release_script_writes()
        for name in sorted(RELEASE_MAINTAINED):
            with self.subTest(path=name):
                self.assertIn(
                    name,
                    written,
                    f"{name} is classified as release-maintained but the "
                    "release script never writes it, so it will drift on the "
                    "next release",
                )

    def test_release_maintained_files_actually_contain_a_version(self):
        """Non-vacuity: an empty file would satisfy the equality test."""
        for name in sorted(RELEASE_MAINTAINED):
            with self.subTest(path=name):
                self.assertTrue(
                    list(version_literals_in(name)),
                    f"{name} is classified as release-maintained but carries "
                    "no version literal at all",
                )


class BuildOutputCollisionTests(unittest.TestCase):
    """No build may overwrite a file the release maintains.

    ``rollup.config.mjs`` was configured to emit ``astronomy-cards.js`` -- the
    shipped, hand-maintained, release-tracked bundle, twelve cards and ~2800
    lines of it -- from three TypeScript sources. ``npm run build`` in that
    directory replaced the product with a minified subset of itself.

    This reads output paths out of the config text because the config cannot be
    imported without its plugins, which CI does not install. That is data
    extraction from a declaration, not a string-absence check: the value is
    resolved to a path and compared against another enumerated set.
    """

    def test_build_configs_were_found(self):
        """A discovery test that finds nothing passes silently forever."""
        self.assertTrue(
            discovered_build_configs(),
            "no build configs discovered, so the collision test below is a "
            "no-op; if the build was removed, remove this test with it",
        )

    def test_no_build_output_collides_with_a_release_maintained_file(self):
        maintained = {Path(name).as_posix() for name in RELEASE_MAINTAINED}
        for config in discovered_build_configs():
            text = (ROOT / config).read_text(encoding="utf-8")
            for output in OUTPUT_FILE.findall(text):
                resolved = (ROOT / config).parent.joinpath(output).resolve()
                relative = resolved.relative_to(ROOT).as_posix()
                with self.subTest(config=config, output=output):
                    self.assertNotIn(
                        relative,
                        maintained,
                        f"{config} writes its build output to {relative}, "
                        "which is a shipped file the release script "
                        "maintains: running the build destroys it",
                    )


if __name__ == "__main__":
    unittest.main()
