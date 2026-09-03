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

KNOWN LIMITS
------------
Declared here so the next person meets them deliberately rather than trusting
the word "every" above:

* **Two-part versions.** ``VERSION_SHAPED`` requires three components, so a
  ``v1.11`` banner is invisible. Every version in this project is three-part,
  which makes this a boundary rather than a bug -- but a two-part literal
  would drift exactly like ``index.ts`` did.
* **Versions assembled at runtime.** ``MAJOR + "." + MINOR`` is invisible to
  any literal sweep by construction. Nothing here can catch it; only the
  release script refusing to match would.
* **Files the sweep does not read.** Handled by declaration rather than by
  silence -- see ``BINARY_SUFFIXES`` and ``SweepCoverageTests``. This was a
  real defect: the original handler caught ``OSError`` alongside
  ``UnicodeDecodeError``, so a corrupted, missing, or unreadable text file
  left the universe as quietly as a PNG, and took every test in this module
  with it while staying green.

AUDITING THIS MODULE
--------------------
Every test here asserts over a universe this module declares: the tracked
file list, ``BINARY_SUFFIXES``, the classification sets. To check whether a
control is doing what its name claims, **mutate a declaration to its
degenerate value and enumerate which tests fire and what they name**:

* ``tracked_files()`` -> ``[]``           (the universe is empty)
* ``BINARY_SUFFIXES`` -> every suffix     (nothing is read)

Three kinds of result, all of which have occurred here:

* Fires and **names files** -- a real control.
* Fires and **names nothing** -- usually a counting restatement of a
  property another test already asserts by naming, carrying a false-red
  mode the exact control does not have. This is how the old
  ``reads_more_than_it_skips`` was identified and removed.
* **Does not fire** -- an unasserted safety property: behaviour that is
  correct by construction with nothing holding it in place. See
  ``test_the_must_find_control_does_not_share_the_sweeps_universe``.

The mutation is the method. Reading the tests will not find these, because
each one looks correct in isolation; what is wrong is a relationship
between a test and the universe it quantifies over.
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

# Files the sweep is allowed not to read, by declaration rather than by
# accident. Skipping on decode failure instead would make a corrupted or
# missing text file indistinguishable from an image.
#
# Keeping this list honest matters more than keeping it short: adding ".js"
# here would silence a real failure, which is why
# test_the_binary_declaration_is_not_an_escape_hatch requires every declared
# suffix to name files that genuinely cannot be decoded.
BINARY_SUFFIXES = (".png",)

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

    Nothing is swallowed. Declared-binary files are skipped by *declaration*;
    everything else is decoded, and both ``UnicodeDecodeError`` and ``OSError``
    propagate. An earlier version caught both and returned, which meant a
    tracked file that was unreadable, missing from disk, or had picked up a
    single non-UTF-8 byte left the sweep's universe in exactly the same way a
    PNG did -- silently, and for all of this module's tests at once.
    """
    if is_declared_binary(relative_path):
        return
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        for match in VERSION_SHAPED.finditer(line):
            prefix = line[max(0, match.start() - 2):match.start()]
            if DEPENDENCY_RANGE.search(prefix):
                continue
            yield lineno, match.group(0), line.strip()


def is_declared_binary(relative_path):
    return Path(relative_path).suffix.lower() in BINARY_SUFFIXES


def partition_tracked_files():
    """Split tracked files into text, declared-binary, and unaccounted-for.

    The third bucket is the point: it is what a bare ``except: return`` threw
    away. Returning it lets a test fail on it instead.
    """
    text, declared_binary, undecodable = [], [], []
    for name in tracked_files():
        if is_declared_binary(name):
            declared_binary.append(name)
            continue
        try:
            (ROOT / name).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            undecodable.append(name)
        else:
            text.append(name)
    return text, declared_binary, undecodable


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


class SweepCoverageTests(unittest.TestCase):
    """The sweep's input set must itself be accounted for.

    Every other test in this module iterates the same set of files. A file
    that leaves that set silently does not weaken one assertion, it weakens
    all of them simultaneously, and they all stay green while it happens.
    """

    def test_every_tracked_file_is_text_or_declared_binary(self):
        _text, _binary, undecodable = partition_tracked_files()
        self.assertEqual(
            [],
            undecodable,
            "these tracked files could not be decoded and are not declared "
            "binary, so they silently left the sweep's universe -- and with "
            "it the universe of every test in this module: "
            f"{undecodable}",
        )

    def test_the_binary_declaration_is_not_an_escape_hatch(self):
        """The obvious way to silence the test above must not work.

        Adding a text suffix to BINARY_SUFFIXES would turn a real failure
        green. Every declared suffix therefore has to name tracked files that
        genuinely cannot be decoded as UTF-8.
        """
        for suffix in BINARY_SUFFIXES:
            with self.subTest(suffix=suffix):
                matching = [
                    name for name in tracked_files()
                    if Path(name).suffix.lower() == suffix
                ]
                self.assertTrue(
                    matching, f"{suffix} is declared binary but matches no file"
                )
                for name in matching:
                    with self.assertRaises(
                        UnicodeDecodeError,
                        msg=f"{name} decodes fine, so {suffix} is not a binary "
                        "suffix and declaring it one hides real files",
                    ):
                        (ROOT / name).read_text(encoding="utf-8")

    def test_unreadable_tracked_files_are_a_fault_not_a_skip(self):
        """OSError must propagate rather than being swallowed as 'binary'.

        A tracked file missing from disk, or unreadable, is a fault. The
        previous handler caught OSError alongside UnicodeDecodeError, so a
        missing file and an image were the same event.
        """
        missing = "does-not-exist-anywhere.js"
        self.assertFalse(
            is_declared_binary(missing),
            "this probe only exercises the read path if its suffix is not "
            "declared binary -- otherwise it is skipped before the open is "
            "attempted and would fail for an unrelated reason",
        )
        with self.assertRaises(OSError):
            list(version_literals_in(missing))

    def test_the_sweep_read_something(self):
        """Non-vacuity, guarding a zero rather than standing as its own gate.

        An earlier version compared ``len(text) > len(binary)``. That was a
        counting restatement of a property already asserted by naming in
        ``test_the_sweep_finds_every_file_the_release_script_writes``, and it
        added a way to go red with no defect present: it was 34 added images
        away from failing. A control that can be red without a defect gets
        relaxed the first time it fires spuriously, and the relaxation looks
        reasonable because the red meant nothing.

        Zero is the only value here that is never legitimate.
        """
        text, _binary, _undecodable = partition_tracked_files()
        self.assertTrue(text, "the sweep read nothing")

    def test_the_must_find_control_does_not_share_the_sweeps_universe(self):
        """An unasserted safety property, now asserted.

        ``test_the_sweep_finds_every_file_the_release_script_writes``
        computes *what the release script writes* minus *what the sweep
        found*. It detects a shrunken sweep only because the first operand
        comes from the release script's own planners rather than from the
        file list the sweep walks. Feed both from ``tracked_files()`` and an
        empty universe yields an empty difference: the control agrees with
        itself and stays green while seeing nothing.

        That independence held by construction and nothing asserted it, so
        the refactor that removed it would have gone unnoticed -- a correct
        behaviour with no test holding it in place, which is a different
        object from a defect and invisible to every technique that starts
        from something being wrong.
        """
        original = globals()["tracked_files"]
        globals()["tracked_files"] = lambda: []
        try:
            survives = paths_the_release_script_writes()
        finally:
            globals()["tracked_files"] = original
        self.assertTrue(
            survives,
            "emptying the sweep's file list also emptied the release "
            "script's, so the must-find control now shares the universe it "
            "is supposed to be auditing and can no longer detect it shrinking",
        )


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
