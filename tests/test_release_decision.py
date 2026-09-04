"""Tests for the release decision.

WHAT THIS MODULE IS GUARDING

Two releases went out -- v1.11.7 and v1.11.8 -- whose entire diff was under
`tests/`. Nothing a user could observe changed, and HACS offered both of them
as updates. The releases are published and are not being retracted: deleting a
tag breaks anyone who pinned it, in order to un-ship a no-op. The damage is a
version number and it is already done. What is worth fixing is the mechanism,
because it fires again on the next `fix:` typed against a test.

The cases below are not invented. They are the four real ranges the workflow
actually evaluated, recorded from git:

    git log  <tag>..<merge> --pretty=format:%s --no-merges
    git diff --name-only <tag>..<merge>

Using history rather than fixtures matters here: two of these four are the
defect firing in production, so the test fails for the exact reason the repo
lost two version numbers, and not for a reason I invented afterwards to be
sure it would fail.

Note `PR_17` carries two subjects. The range is `LAST_TAG..HEAD`, so #16's
commit -- correctly skipped at the time -- was still sitting in the range when
#17 landed, and appears in v1.11.8's published notes. A skipped commit is not
dropped, it accumulates. That is correct behaviour and worth pinning down,
because the obvious wrong fix for this defect is to make skipped commits
disappear.

ON THE LAST TEST IN THIS FILE

`test_the_workflow_has_exactly_one_decider` reads `release.yml` as text, which
looks like the string-checking anti-pattern the rest of this suite exists to
avoid. The distinction: elsewhere the program can be run, so reading its source
is a weaker measurement than executing it. A GitHub Actions workflow cannot be
executed here at all, and its text *is* its behaviour -- it is configuration,
not prose about configuration. The hazard being guarded is specific and is this
chain's recurring one: `decide()` could be perfectly correct and simply not
wired up, leaving the inline bash as a second, silent decider.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from harness import COMPONENT_DIR, load_component_module  # noqa: E402

import release_decision  # noqa: E402
from release_decision import (  # noqa: E402
    NOT_SHIPPING,
    SHIPPING,
    Commit,
    bump_from_subjects,
    changelog,
    decide,
    derived_shipping,
    installed_roots,
    ships,
    top_level,
)

package_init = load_component_module("__init__")


class Range(tuple):
    """A recorded historical range: what the workflow saw, and what it did."""

    def __new__(cls, label, subjects, paths, should_release, actually_did):
        return super().__new__(cls, (label, subjects, paths, should_release, actually_did))

    label = property(lambda self: self[0])
    subjects = property(lambda self: self[1])
    paths = property(lambda self: self[2])
    should_release = property(lambda self: self[3])
    actually_did = property(lambda self: self[4])


HISTORY = (
    Range(
        "PR #15 (842dc47..b727825) -> published v1.11.7",
        ["fix: make the version sweep's skip path fail open instead of silent (#15)"],
        ["tests/test_version_literals.py"],
        should_release=False,
        actually_did=True,
    ),
    Range(
        "PR #16 (7541424..6031569) -> correctly skipped",
        ["test: remove a restatement, assert a coincidence, record the method (#16)"],
        ["tests/test_version_literals.py"],
        should_release=False,
        actually_did=False,
    ),
    Range(
        "PR #17 (7541424..edbfdbd) -> published v1.11.8",
        [
            "fix: a failed import in the harness must not be served from cache (#17)",
            "test: remove a restatement, assert a coincidence, record the method (#16)",
        ],
        ["tests/harness.py", "tests/test_harness.py", "tests/test_version_literals.py"],
        should_release=False,
        actually_did=True,
    ),
    Range(
        "PR #13 (63031c7..4ad0a04) -> published v1.11.5, correctly",
        ["fix: bring deepsky-cards.js under release versioning (#13)"],
        [
            "custom_components/nasa_astronomy/deepsky-cards.js",
            "scripts/bump_version.py",
            "tests/test_cards_resource_version.py",
            "www/community/astronomy-cards/deepsky-cards.js",
        ],
        should_release=True,
        actually_did=True,
    ),
    Range(
        # This one is the whole argument for classifying `scripts/` as
        # not-shipping, so it is recorded rather than left implicit. It was
        # found by replaying every release range through the fixed predicate,
        # not by reading the diff -- a third instance nobody had noticed.
        "PR #12 (v1.11.3..45385bc) -> published v1.11.4",
        ["fix: make a version bump atomic so an aborted release cannot half-happen (#12)"],
        ["scripts/bump_version.py", "tests/test_cards_resource_version.py"],
        should_release=False,
        actually_did=True,
    ),
    Range(
        # Found by the sibling review, and the reason `www/` changed buckets.
        # It is the only range in the repository's history where a www/ path
        # was the deciding vote, and the files were two TypeScript sources that
        # nothing compiles plus a rollup config -- build machinery, which the
        # same argument that exempts `scripts/` says cannot ship.
        "PR #14 (v1.11.5..22c0a17) -> published v1.11.6",
        ["fix: sweep every version literal, and stop the build eating the bundle (#14)"],
        [
            ".gitignore",
            "scripts/bump_version.py",
            "tests/test_version_literals.py",
            "www/community/astronomy-cards/index.ts",
            "www/community/astronomy-cards/rollup.config.mjs",
        ],
        should_release=False,
        actually_did=True,
    ),
)

BUMP_IMPLYING_SUBJECTS = (
    "fix: something",
    "perf: something",
    "refactor: something",
    "feat: something",
    "feat!: something",
)


def probes(path_root: str) -> tuple[str, ...]:
    """Realistic diff entries for a classified root.

    Both the bare root (it may be a file, like `hacs.json`) and a nested path
    (it may be a directory, like `.github/workflows/release.yml`), because the
    classification is consulted with whatever git actually prints.
    """
    return (path_root, f"{path_root}/nested/file.txt")


def tracked_top_level_paths() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return {top_level(p) for p in out.splitlines() if p.strip()}


class HistoricalRangeTests(unittest.TestCase):
    """The defect, replayed against the four ranges that produced it."""

    def test_every_recorded_range_decides_correctly(self):
        wrong = []
        for case in HISTORY:
            got = decide(case.subjects, case.paths)
            if got.release != case.should_release:
                wrong.append(
                    f"{case.label}\n"
                    f"      expected release={case.should_release} "
                    f"got release={got.release} bump={got.bump!r}\n"
                    f"      reason: {got.reason}\n"
                    f"      paths:  {', '.join(case.paths)}"
                )
        self.assertFalse(
            wrong,
            "the decision is wrong for %d of %d recorded ranges:\n    %s"
            % (len(wrong), len(HISTORY), "\n    ".join(wrong)),
        )

    def test_a_skipped_commit_still_counts_toward_the_next_release(self):
        """#16 was skipped; its subject was still in range when #17 landed.

        Passes before and after the fix. It pins the behaviour that the wrong
        fix -- dropping skipped commits so they cannot trigger anything -- would
        break, which would silently lose them from the changelog.
        """
        pr17 = HISTORY[2]
        self.assertIn(
            "test: remove a restatement, assert a coincidence, record the method (#16)",
            pr17.subjects,
            "the recorded range no longer carries the earlier skipped commit",
        )
        self.assertEqual(
            "patch",
            bump_from_subjects(pr17.subjects),
            "a range mixing a skipped type with fix: should still size as patch",
        )


class ShippingPredicateTests(unittest.TestCase):
    """The general property, not the four historical samples."""

    def test_no_commit_type_can_release_a_change_that_ships_nothing(self):
        offenders = []
        for subject in BUMP_IMPLYING_SUBJECTS:
            for path_root in sorted(NOT_SHIPPING):
                for probe in probes(path_root):
                    got = decide([subject], [probe])
                    if got.release:
                        offenders.append(f"{subject!r} + {probe!r} -> {got.bump}")
        self.assertFalse(
            offenders,
            "%d combinations release without shipping anything:\n    %s"
            % (len(offenders), "\n    ".join(offenders)),
        )

    def test_a_shipping_change_still_releases(self):
        """The other direction. Without this, `return False` passes everything.

        Passes before and after the fix, which is the point: it shows the suite
        is discriminating rather than uniformly red, and it forbids the lazy
        fix of never releasing at all.
        """
        missed = []
        for subject in BUMP_IMPLYING_SUBJECTS:
            for path_root in sorted(SHIPPING):
                for probe in probes(path_root):
                    got = decide([subject], [probe])
                    if not got.release:
                        missed.append(f"{subject!r} + {probe!r} -> {got.reason}")
        self.assertFalse(
            missed,
            "%d shipping changes would not be released:\n    %s"
            % (len(missed), "\n    ".join(missed)),
        )

    def test_a_mixed_change_releases(self):
        """Touching a test and a shipped file is a release. The common case."""
        got = decide(["fix: x"], ["tests/test_x.py", "custom_components/y/z.py"])
        self.assertTrue(got.release, f"a mixed diff was skipped: {got.reason}")

    def test_bump_sizing_is_unchanged(self):
        """Non-vacuity: sizing is orthogonal to shipping and must not move."""
        self.assertEqual("major", bump_from_subjects(["feat!: drop a thing"]))
        self.assertEqual("minor", bump_from_subjects(["feat: add a thing"]))
        self.assertEqual("patch", bump_from_subjects(["fix: mend a thing"]))
        self.assertEqual("none", bump_from_subjects(["test: check a thing"]))
        self.assertEqual("none", bump_from_subjects(["docs: write a thing"]))
        self.assertEqual("none", bump_from_subjects([]))


class ClassificationCorrectnessTests(unittest.TestCase):
    """Whether the classification is *right*, not merely total.

    The completeness control below is a partition check: it fires when a new
    top-level path appears in neither map, and it stays green forever on a path
    filed in the wrong bucket -- including on the day the map is written. It
    guards against the map rotting and cannot notice a map that shipped
    pre-rotted, which is what happened: `www/`, `lovelace/`, `icon.png`,
    `logo.png` and `info.md` were classified as shipping by intuition about
    what looks like product, and none of them reaches an installation.

    That is the same defect the module exists to remove, one level up. The
    declared map was consulted; HACS's install convention and
    `_deploy_cards_to_www` were authoritative and were never asked. So the
    shipping set is now derived from those, and what remains hand-written is
    only the list of things that ship nothing -- where being wrong costs a
    release that did not happen rather than one that should not have.
    """

    def test_every_shipping_path_is_installed_or_displayed(self):
        """A regression guard on the name, not a restatement of the derivation.

        `SHIPPING` is now computed, so this cannot fail while it stays computed
        -- and a test that cannot fail is the defect removed in PR #16. It is
        kept because it *can* fail, on exactly one change: someone replacing
        the derivation with a hand-written map again. Verified by mutation
        rather than assumed -- restoring the old literal map makes this name
        all five entries -- and that regression is worth a red test, because it
        is the one that happened.
        """
        derived = derived_shipping()
        unjustified = sorted(set(SHIPPING) - set(derived))
        self.assertFalse(
            unjustified,
            "%d paths are classified as shipping but are neither installed by "
            "HACS nor displayed by it, so a change to them alone can release a "
            "version that reaches nobody:\n    %s"
            % (len(unjustified), "\n    ".join(unjustified)),
        )

    def test_the_browser_facing_bundles_live_inside_an_installed_root(self):
        """Why `www/` ships nothing, asserted instead of argued.

        `_deploy_cards_to_www` copies the card bundles into a user's config
        from `Path(__file__).parent`, the installed package directory. So the
        bundles a browser loads are the ones under `custom_components/`, and
        the repository's top-level `www/` copies are read by nobody.

        That is the fact the derivation rests on and cannot check about
        itself. If the integration were ever changed to deploy from somewhere
        else, or the bundles were moved out of the package, the derived
        shipping set would be wrong -- and this goes red rather than the
        classification silently drifting.
        """
        installed = set(installed_roots())
        deployed = list(package_init.DEPLOYED_FILENAMES)
        missing = [
            name for name in deployed if not (COMPONENT_DIR / name).is_file()
        ]
        self.assertFalse(
            missing,
            "%d file(s) the integration deploys to a user's browser are not "
            "inside its own package, so they must ship from somewhere the "
            "derivation does not know about: %s"
            % (len(missing), ", ".join(missing)),
        )
        self.assertIn(
            top_level(COMPONENT_DIR.relative_to(ROOT).as_posix()),
            installed,
            "the package the integration deploys from is not one of the roots "
            "HACS installs, so the derived shipping set is wrong",
        )

    def test_the_readme_ships_whatever_hacs_json_says_about_rendering(self):
        """`render_readme` is read by this repository and by nobody else.

        HACS picks the file it renders from a hardcoded list of README
        spellings -- `hacs/integration`, `HacsRepository.get_info_md_content`,
        where the variant list is built from `name: str = "readme"`. The
        `render_readme` key is still accepted by its schema validator and is no
        longer consulted when choosing the file, which is why `info.md` renders
        nowhere however it is configured.

        So gating on that key reproduced the defect this module exists to
        remove, inside the module: the declared source of truth was read while
        the deciding one was somewhere else. Setting `render_readme: false`
        would have dropped README.md out of the shipping set while HACS carried
        on rendering it, and a genuine documentation release would have been
        silently withheld.

        This passes now because nothing reads the key. It goes red the moment
        someone reintroduces a gate on it.
        """
        roots = release_decision.displayed_roots(
            tracked=["README.md", "hacs.json"],
        )
        self.assertIn(
            "README.md",
            roots,
            "README.md stopped shipping because hacs.json disabled a key HACS "
            "does not consult; a docs release would be withheld while every "
            "user still sees the change",
        )

    def test_the_readme_is_only_shipping_when_the_repository_has_one(self):
        """The other direction, so the rule is not `always true`."""
        roots = release_decision.displayed_roots(
            tracked=["hacs.json", "custom_components/x/manifest.json"],
        )
        self.assertNotIn(
            "README.md",
            roots,
            "a README that does not exist was classified as shipping",
        )

    def test_nothing_that_ships_is_declared_not_shipping(self):
        """The other direction: a real shipped path filed as inert."""
        derived = derived_shipping()
        suppressed = sorted(set(NOT_SHIPPING) & set(derived))
        self.assertFalse(
            suppressed,
            "%d paths reach a user but are declared not-shipping, so genuine "
            "releases would be silently withheld:\n    %s"
            % (len(suppressed), "\n    ".join(suppressed)),
        )

    def test_the_derivation_found_the_integration(self):
        """Guards a zero.

        If the manifest scan finds nothing, the shipping set is empty, every
        change looks inert and the repository silently stops releasing
        altogether. That failure is invisible in every other test here, all of
        which would go green.
        """
        installed = installed_roots()
        self.assertTrue(
            installed,
            "no manifest.json was discovered, so nothing is considered "
            "installable and no release could ever be cut again",
        )

    def test_the_derivation_does_not_claim_everything(self):
        """The opposite degenerate value, which would restore the old defect."""
        derived = set(derived_shipping())
        everything = tracked_top_level_paths()
        self.assertNotEqual(
            everything,
            derived,
            "every tracked path is considered shipping, which is the "
            "pre-fix behaviour wearing a derivation",
        )


class ClassificationCompletenessTests(unittest.TestCase):
    """The maps are hand-written, so they get a control that they are total."""

    def test_every_tracked_path_is_classified(self):
        unclassified = sorted(
            tracked_top_level_paths() - set(SHIPPING) - set(NOT_SHIPPING)
        )
        self.assertFalse(
            unclassified,
            "%d tracked top-level paths are classified by neither map, so a "
            "change to them cannot be reasoned about:\n    %s"
            % (len(unclassified), "\n    ".join(unclassified)),
        )

    def test_the_classification_is_not_vacuous(self):
        """Guards a zero. If ls-files returns nothing, completeness is trivial."""
        self.assertTrue(tracked_top_level_paths(), "no tracked files were found")

    def test_nothing_is_classified_twice(self):
        both = sorted(set(SHIPPING) & set(NOT_SHIPPING))
        self.assertFalse(both, f"classified as both shipping and not: {both}")

    def test_every_classification_states_a_reason(self):
        """An exemption that cannot say why it is exempt cannot be reviewed."""
        silent = sorted(
            path
            for path, why in {**SHIPPING, **NOT_SHIPPING}.items()
            if not why or not why.strip()
        )
        self.assertFalse(silent, f"classified with no stated reason: {silent}")


class ChangelogTests(unittest.TestCase):
    """The notes describe the release, so they answer the same question it did.

    The module decides whether a change reaches a user and then writes a
    changelog headed "What's Changed". Until now those two used different
    rules: the decision consulted the diff, and the notes listed everything.
    v1.11.8 shipped nothing at all and still published a two-item changelog.

    These tests are written against `changelog()` as a function of commits
    rather than against the emitted text of any one release, so they stay true
    when the repository's history grows and cannot be satisfied by editing a
    fixture to match the output.
    """

    HEADING = "### Also in this release"

    def _ranges(self):
        """Every tag-to-tag range in the repository, plus the open one.

        Discovered rather than listed. The failure mode being guarded against
        is a commit shape nobody thought to write down, so the fixture is the
        actual history.
        """
        tags = release_decision._git(
            "tag", "--list", "--sort=v:refname"
        ).split()
        self.assertGreater(len(tags), 10, "no tags found -- the fixture is empty")
        pairs = list(zip(tags, tags[1:])) + [(tags[-1], "HEAD")]
        for older, newer in pairs:
            raw = release_decision._git(
                "log",
                f"{older}..{newer}",
                f"--pretty=format:{release_decision._RECORD}%s",
                "--name-only",
                "--no-merges",
            )
            yield f"{older}..{newer}", release_decision._parse_log(raw)

    def test_every_commit_in_every_real_range_appears_exactly_once(self):
        """Partition, not filter. Dropping a commit would be the silent skip."""
        checked = 0
        for label, commits in self._ranges():
            if not commits:
                continue
            checked += 1
            body = changelog(commits)
            for commit in commits:
                self.assertEqual(
                    body.count(f"- {commit.subject}"),
                    1,
                    f"{label}: {commit.subject!r} appears "
                    f"{body.count(f'- {commit.subject}')} times in the notes, "
                    "so the changelog either dropped a commit or listed it twice",
                )
        self.assertGreater(checked, 5, "too few non-empty ranges to be evidence")

    def test_a_commit_is_filed_under_the_heading_exactly_when_it_ships_nothing(self):
        """The notes and the gate must not be able to disagree.

        This is the assertion the old renderer cannot satisfy: it had no second
        section, so every non-shipping commit sat under a heading claiming it
        changed something for the reader.
        """
        misfiled = []
        for label, commits in self._ranges():
            if not commits:
                continue
            body = changelog(commits)
            head, _, tail = body.partition(self.HEADING)
            for commit in commits:
                entry = f"- {commit.subject}"
                internal = entry in tail
                if bool(ships(commit.paths)) == internal:
                    misfiled.append(
                        f"{label}: {commit.subject!r} touched "
                        f"{sorted(commit.paths)} -> ships="
                        f"{bool(ships(commit.paths))} but the notes filed it "
                        f"as {'internal' if internal else 'shipping'}"
                    )
        self.assertTrue(
            not misfiled,
            "the changelog files commits differently from the release gate:\n    "
            + "\n    ".join(misfiled),
        )

    def test_the_heading_is_absent_when_every_commit_ships(self):
        """An empty section is noise, and noise is what this test suite is for."""
        body = changelog(
            [
                Commit("fix: a real change", ("custom_components/x/sensor.py",)),
                Commit("feat: another", ("custom_components/x/camera.py",)),
            ]
        )
        self.assertTrue(
            self.HEADING not in body,
            "the changelog printed an 'also in this release' heading with "
            "nothing under it:\n" + body,
        )

    def test_a_mixed_release_separates_the_two(self):
        commits = [
            Commit("fix: the shipping one", ("custom_components/x/sensor.py",)),
            Commit("test: the internal one", ("tests/test_x.py",)),
        ]
        body = changelog(commits)
        head, sep, tail = body.partition(self.HEADING)
        self.assertTrue(sep, "a mixed release produced no separation:\n" + body)
        self.assertTrue(
            "- fix: the shipping one" in head,
            "the shipping commit was not listed above the heading:\n" + body,
        )
        self.assertTrue(
            "- test: the internal one" in tail,
            "the internal commit was not listed below the heading:\n" + body,
        )

    def test_the_notes_name_every_subject(self):
        """Non-vacuity. This passed before the partition existed and after it.

        A reviewer looking at a uniformly red suite cannot tell a discriminating
        test from a broken import, so at least one assertion here has to be
        indifferent to the change being made.
        """
        for label, commits in self._ranges():
            for commit in commits:
                self.assertTrue(
                    commit.subject in changelog(commits),
                    f"{label}: {commit.subject!r} is missing from the notes "
                    "entirely, which no version of this renderer should do",
                )

    def test_v1_11_8_is_the_worked_example(self):
        """The defect, measured on the release that actually published it.

        Recorded because it is the reason this exists: v1.11.8's two commits
        touched only `tests/`, and its published notes said "What's Changed".
        """
        raw = release_decision._git(
            "log",
            "v1.11.7..v1.11.8",
            f"--pretty=format:{release_decision._RECORD}%s",
            "--name-only",
            "--no-merges",
        )
        commits = [
            c
            for c in release_decision._parse_log(raw)
            if not c.subject.startswith("release:")
        ]
        self.assertEqual(len(commits), 2, "the recorded range changed shape")
        self.assertFalse(
            [c for c in commits if ships(c.paths)],
            "v1.11.8 is recorded here as a release that shipped nothing; if "
            "that is no longer true the example needs replacing",
        )
        body = changelog(commits)
        self.assertTrue(
            self.HEADING in body,
            "the release that shipped nothing still renders as though it did:\n"
            + body,
        )


class LogParsingTests(unittest.TestCase):
    """`--name-only` output is a format, so it is tested as one."""

    def test_a_recorded_log_splits_into_commits_and_paths(self):
        raw = (
            "\x1edocs: one (#21)\nscripts/release_decision.py\n\n"
            "\x1efix: two (#20)\nscripts/release_decision.py\n"
            "tests/test_release_decision.py\n"
        )
        self.assertEqual(
            release_decision._parse_log(raw),
            [
                Commit("docs: one (#21)", ("scripts/release_decision.py",)),
                Commit(
                    "fix: two (#20)",
                    ("scripts/release_decision.py", "tests/test_release_decision.py"),
                ),
            ],
        )

    def test_a_commit_touching_nothing_keeps_its_subject(self):
        parsed = release_decision._parse_log("\x1echore: empty\n")
        self.assertEqual(parsed, [Commit("chore: empty", ())])

    def test_an_empty_range_parses_to_nothing(self):
        self.assertEqual(release_decision._parse_log(""), [])

    def test_the_subjects_match_the_plain_log_for_the_open_range(self):
        """The parser must not change what the gate sees.

        `decide()` is fed subjects from this walk. If the parse disagrees with
        `git log --pretty=format:%s` then moving to `--name-only` silently
        altered the release decision, which is the one thing this change was
        not allowed to do.
        """
        last_tag = release_decision._git(
            "describe", "--tags", "--abbrev=0"
        ).strip()
        plain = [
            s
            for s in release_decision._git(
                "log", f"{last_tag}..HEAD", "--pretty=format:%s", "--no-merges"
            ).splitlines()
            if s.strip()
        ]
        raw = release_decision._git(
            "log",
            f"{last_tag}..HEAD",
            f"--pretty=format:{release_decision._RECORD}%s",
            "--name-only",
            "--no-merges",
        )
        self.assertEqual(
            [c.subject for c in release_decision._parse_log(raw)],
            plain,
            "the --name-only walk yields different subjects from the plain "
            "walk, so the release gate now sees a different range",
        )


class ShallowCheckoutTests(unittest.TestCase):
    """A gate that cannot see the history must not fall back to publishing.

    `git describe` fails identically for a repository that was never tagged and
    one whose tags were not fetched. `collect()` used to treat both as a first
    release, and `ls-files` then claims every tracked file as new. Measured on
    a real depth-1 clone of this repository before the fix:

        decision: RELEASE (patch)
        reason:   a patch bump, and 25 shipped file(s) changed

    The gate that had suppressed five consecutive releases published.
    """

    def _run(self, cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        )

    def _new_origin(self, tmp: Path) -> Path:
        origin = tmp / "origin"
        origin.mkdir()
        self._run(origin, "init", "-q", "-b", "main")
        self._run(origin, "config", "user.email", "t@example.invalid")
        self._run(origin, "config", "user.name", "t")
        return origin

    def _commit(self, origin: Path, message: str, name: str = "a.txt") -> None:
        (origin / name).write_text(message, encoding="utf-8")
        self._run(origin, "add", "-A")
        self._run(origin, "commit", "-q", "-m", message)

    def _linear_origin(self, tmp: Path, gap: int) -> Path:
        origin = self._new_origin(tmp)
        self._commit(origin, "root")
        self._run(origin, "tag", "v0.0.1")
        for n in range(gap):
            self._commit(origin, f"c{n}")
        assert (
            self._run(origin, "rev-list", "--count", "v0.0.1..HEAD").stdout.strip()
            == str(gap)
        ), "the fixture did not build the gap it says it did"
        return origin

    def _merged_origin(self, tmp: Path) -> Path:
        """History where the commit count and the path length disagree."""
        origin = self._new_origin(tmp)
        self._commit(origin, "first")
        self._run(origin, "tag", "v0.0.1")
        self._run(origin, "checkout", "-q", "-b", "side")
        self._commit(origin, "side work", "s.txt")
        self._run(origin, "checkout", "-q", "main")
        self._commit(origin, "after the tag")
        self._run(origin, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        self._commit(origin, "final")
        return origin

    def _catchup_merge_origin(self, tmp: Path) -> Path:
        """History that breaks the --no-merges bound, built only with --no-ff.

                P0
              /  |  \\
            U1   V1   S1
              \\ /
               A = merge(U1, V1)   <- tag v0.0.1
                     M1 = merge(S1, U1)
                     M2 = merge(M1, V1)
                     M3 = merge(M2, A)   <- HEAD

        A long-lived branch that forked before the tag and caught up by merging
        the upstream branches in one at a time before merging the release --
        what people do to take conflicts in pieces. The range holds three
        merges and one ordinary commit, so the `--no-merges` count is 1 while
        the walk boundary is 4.

        No plumbing, no forced parents: every merge here is a plain
        `git merge --no-ff` that a person could type.
        """
        origin = self._new_origin(tmp)
        self._commit(origin, "P0", "P0.txt")
        self._run(origin, "branch", "base")
        self._run(origin, "checkout", "-qb", "u")
        self._commit(origin, "U1", "U1.txt")
        self._run(origin, "checkout", "-qb", "v", "base")
        self._commit(origin, "V1", "V1.txt")
        self._run(origin, "checkout", "-q", "u")
        self._run(origin, "merge", "-q", "--no-ff", "v", "-m", "A")
        self._run(origin, "tag", "v0.0.1")
        self._run(origin, "checkout", "-qb", "s", "base")
        self._commit(origin, "S1", "S1.txt")
        self._run(origin, "merge", "-q", "--no-ff", "u~1", "-m", "M1")
        self._run(origin, "merge", "-q", "--no-ff", "v", "-m", "M2")
        self._run(origin, "merge", "-q", "--no-ff", "v0.0.1", "-m", "M3")
        return origin

    def _asymmetric_origin(self, tmp: Path) -> Path:
        """History where the two boundaries disagree.

        A(v0.0.1) - B(feat) - C - D - E - M(HEAD)
                 \\________________________ F __/

        The side branch is cut at the *tag* and merged after the mainline has
        moved on, so the tag has a short path while the range still has a long
        one. In the merged fixture above, the tag is the farthest thing in the
        range, so describe-success already implies a complete walk and the two
        boundaries cannot be told apart. Here they can.
        """
        origin = self._new_origin(tmp)
        self._commit(origin, "fix: root")
        self._run(origin, "tag", "v0.0.1")
        self._commit(origin, "feat: on the long path", "b.txt")
        for name in ("c", "d", "e"):
            self._commit(origin, f"fix: {name}", f"{name}.txt")
        self._run(origin, "checkout", "-q", "-b", "side", "v0.0.1")
        self._commit(origin, "fix: shortcut", "f.txt")
        self._run(origin, "checkout", "-q", "main")
        self._run(origin, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        return origin

    def _subjects(self, repo: Path, tag: str = "v0.0.1") -> list[str]:
        out = self._run(
            repo, "log", f"{tag}..HEAD", "--pretty=%s", "--no-merges"
        ).stdout
        return [line for line in out.split("\n") if line.strip()]

    def _walk_boundary(self, tmp: Path, origin: Path) -> int:
        """Shallowest depth whose subject list matches a full clone.

        Distinct from _shallowest_depth_that_describes: that one answers the
        `git diff` question, this one answers the `git log` question, and the
        whole point is that they are not the same number.
        """
        truth = self._subjects(origin)
        total = int(self._run(origin, "rev-list", "--count", "HEAD").stdout.strip())
        for depth in range(1, total + 2):
            clone = tmp / f"walk{depth}"
            self._run(
                tmp, "clone", "-q", "--depth", str(depth), origin.as_uri(), str(clone)
            )
            self._run(clone, "fetch", "--tags", "-q")
            described = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=clone,
                capture_output=True,
                text=True,
            )
            if described.returncode == 0 and self._subjects(clone) == truth:
                return depth
        raise AssertionError(
            "no depth up to the full history reproduced the full subject list, "
            "so this probe is not measuring what it claims to"
        )

    def _shortest_path_length(self, origin: Path, tag: str = "v0.0.1") -> int:
        """Commits on the shortest HEAD->tag path, counting both ends.

        This is the thing that generates the boundary. The docstring used to
        print an observed depth, then a formula that happened to match it on
        linear history. Computing the generator means the test says the same
        thing on every history shape instead of on the one it was written
        against.
        """
        target = self._run(origin, "rev-parse", f"{tag}^{{commit}}").stdout.strip()
        parents = {}
        for line in self._run(origin, "rev-list", "--parents", "HEAD").stdout.split("\n"):
            shas = line.split()
            if shas:
                parents[shas[0]] = shas[1:]
        head = self._run(origin, "rev-parse", "HEAD").stdout.strip()
        frontier, seen, distance = [head], {head}, 1
        while frontier:
            if target in frontier:
                return distance
            nxt = []
            for sha in frontier:
                for parent in parents.get(sha, []):
                    if parent not in seen:
                        seen.add(parent)
                        nxt.append(parent)
            frontier, distance = nxt, distance + 1
        raise AssertionError(
            f"{tag} is not an ancestor of HEAD in this fixture, so there is no "
            "path whose length could be the boundary"
        )

    def _shallowest_depth_that_describes(self, tmp: Path, origin: Path) -> int:
        """Probe for the real boundary instead of assuming a formula for it.

        Both callers used to pick a depth from a formula. One of those formulas
        was wrong for merged history and the test still passed, because it had
        chosen a depth above the boundary rather than on it. Measuring removes
        the assumption from the test that exists to check the assumption.
        """
        total = int(
            self._run(origin, "rev-list", "--count", "HEAD").stdout.strip()
        )
        for depth in range(1, total + 2):
            clone = tmp / f"probe{depth}"
            self._run(
                tmp,
                "clone",
                "-q",
                "--depth",
                str(depth),
                origin.as_uri(),
                str(clone),
            )
            self._run(clone, "fetch", "--tags", "-q")
            if (
                subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    cwd=clone,
                    capture_output=True,
                    text=True,
                ).returncode
                == 0
            ):
                return depth
        raise AssertionError(
            "no depth up to the full history could describe the tag, so this "
            "probe is not measuring what it claims to"
        )

    def test_the_policy_covers_every_combination(self):
        """Four states, enumerated, because three of them look alike."""
        self.assertEqual(release_decision.range_start("v1.2.3", False), "v1.2.3")
        self.assertIsNone(release_decision.range_start("", False))
        with self.assertRaises(release_decision.ShallowCheckoutError):
            release_decision.range_start("", True)
        with self.assertRaises(release_decision.ShallowCheckoutError):
            release_decision.range_start("v1.2.3", True)

    def test_a_tagged_full_clone_is_unaffected(self):
        """Non-vacuity: true before the guard existed and after it.

        This is the path every real release takes. If the guard had changed it,
        the suite would be red for the right reason and the fix would be wrong.
        """
        self.assertEqual(
            release_decision.range_start("v1.11.8", False),
            "v1.11.8",
            "the ordinary case stopped working, which no shallow-clone guard "
            "should be able to do",
        )

    def test_this_repository_is_not_shallow_and_the_probe_agrees(self):
        self.assertFalse(
            release_decision._repo_is_shallow(),
            "the working repository reports itself shallow, so either the "
            "probe is wrong or the fixture-bearing history is missing",
        )

    def test_git_really_does_behave_this_way_on_a_shallow_clone(self):
        """The premise, measured rather than recalled -- and the corrected one.

        The guard's first version justified itself with "the tags were not
        fetched". That is the wrong mechanism, and this test is what proves it:
        the tags are fetched below, all of them, and `describe` still fails.
        What matters is whether the tagged *commit* is inside the graft, so the
        tag list is not a safe proxy and this function is not allowed to use it.

        Both sides of the boundary are pinned, because the second one refutes a
        stronger claim I made and had to withdraw -- see the sibling test.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin = Path(tmp) / "origin"
            origin.mkdir()
            run = lambda *a, **k: subprocess.run(  # noqa: E731
                ["git", *a],
                cwd=k.get("cwd", origin),
                check=True,
                capture_output=True,
                text=True,
            )
            run("init", "-q", "-b", "main")
            run("config", "user.email", "t@example.invalid")
            run("config", "user.name", "t")

            def commit(message: str) -> None:
                (origin / "a.txt").write_text(message, encoding="utf-8")
                run("add", "-A")
                run("commit", "-q", "-m", message)

            commit("first")
            run("tag", "v0.0.1")
            for n in range(5):
                commit(f"after the tag {n}")

            clone = Path(tmp) / "clone"
            run("clone", "-q", "--depth", "1", origin.as_uri(), str(clone), cwd=tmp)
            run("fetch", "--tags", "-q", cwd=clone)

            shallow = run(
                "rev-parse", "--is-shallow-repository", cwd=clone
            ).stdout.strip()
            self.assertEqual(
                shallow, "true", "a --depth 1 clone did not report as shallow"
            )
            self.assertIn(
                "v0.0.1",
                run("tag", "--list", cwd=clone).stdout.split(),
                "the tags were not fetched, so this clone cannot show that "
                "present tags are still not enough -- which is the whole point",
            )
            described = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=clone,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                described.returncode,
                0,
                "git describe succeeded with the tag present but the tagged "
                "commit outside the graft, so the guard's stated mechanism is "
                "wrong and the docstring needs rewriting before this passes",
            )
            # The end of the chain: given exactly what git reports there, the
            # policy refuses instead of claiming a first release.
            with self.assertRaises(release_decision.ShallowCheckoutError):
                release_decision.range_start("", shallow == "true")

    def test_a_deep_enough_clone_computes_the_range_correctly(self):
        """The claim this module refuses to make: bounded depth is not wrong.

        An earlier justification for refusing the whole shallow space said a
        bounded depth could leave `describe` succeeding while the range stayed
        unwalkable. It cannot: `describe` walks ancestors from HEAD, so if it
        finds a tag the tag is reachable and the range walks. The two states
        exclude each other, and this pins that -- if it ever goes red, the
        refusal is catching real breakage rather than being conservative, and
        the docstring above is the thing that needs revisiting.

        The refusal stays regardless, for the reason measured in that
        docstring: below the boundary the gate does not degrade, it inverts.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._merged_origin(Path(tmp))

            truth = self._run(
                origin, "log", "v0.0.1..HEAD", "--pretty=%s", "--no-merges"
            ).stdout.split("\n")
            truth = [line for line in truth if line.strip()]

            clone = Path(tmp) / "clone"
            # Measured, not derived. The first version hardcoded 20 against
            # five commits -- safe, but safe by margin. The second derived
            # gap + 1, which is the wrong formula for this fixture precisely
            # because it contains a merge, and the test still passed because
            # gap + 1 lands above the boundary rather than on it. So the depth
            # is probed, and the clone sits exactly at the shallowest depth
            # that can see the tag.
            depth = self._shallowest_depth_that_describes(Path(tmp), origin)
            self._run(
                Path(tmp),
                "clone",
                "-q",
                "--depth",
                str(depth),
                origin.as_uri(),
                str(clone),
            )
            self._run(clone, "fetch", "--tags", "-q")

            described = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=clone,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                described.returncode,
                0,
                "a clone deep enough to contain the tag could not describe it, "
                "so this test is no longer measuring the case it names",
            )
            walked = self._run(
                clone,
                "log",
                f"{described.stdout.strip()}..HEAD",
                "--pretty=%s",
                "--no-merges",
            ).stdout.split("\n")
            self.assertEqual(
                [line for line in walked if line.strip()],
                truth,
                "a clone whose describe succeeded still walked a different "
                "range than the full history, which would mean a successful "
                "describe is not sufficient after all",
            )

    def test_the_describe_boundary_follows_the_shortest_path(self):
        """The number the docstring used to print, re-derived instead.

        Named for the question it answers. This is the depth at which
        `git describe` starts working, which is what `git diff start..HEAD`
        needs -- and it is NOT the depth at which `git log start..HEAD` becomes
        complete. That second boundary is measured in the test below; naming
        this one "the boundary" was how a false claim got into the docstring.

        `range_start` describes the shallowest workable depth as the length of
        the shortest path from HEAD to the tagged commit. That replaced a table
        of measured depths against a named tag, which was accurate when written
        and started decaying on the next commit.

        The first replacement was itself too strong: it said
        (commits since the tag) + 1, which is true only on linear history. With
        a merge in the range the commit count exceeds the path length and the
        boundary follows the path. So the assertion here is against the
        generator -- the shortest path, computed by walking parents -- and the
        merge case additionally pins that the convenient formula is wrong, so
        nobody restores it.
        """
        for gap in (1, 2, 5):
            with self.subTest(shape="linear", gap=gap):
                with tempfile.TemporaryDirectory() as tmp:
                    origin = self._linear_origin(Path(tmp), gap)
                    found = self._shallowest_depth_that_describes(Path(tmp), origin)
                    self.assertEqual(
                        found,
                        self._shortest_path_length(origin),
                        "the shallowest depth that can see the tag is not the "
                        "length of the shortest path to it",
                    )
                    # Non-vacuity for the merge case below: on linear history
                    # the two formulas agree, so this passes whichever one is
                    # in force and shows the merge failure is discriminating.
                    self.assertEqual(
                        found,
                        gap + 1,
                        f"on linear history with {gap} commit(s) since the tag "
                        f"the boundary should be {gap + 1}",
                    )

        with self.subTest(shape="merge"):
            with tempfile.TemporaryDirectory() as tmp:
                origin = self._merged_origin(Path(tmp))
                count = int(
                    self._run(
                        origin, "rev-list", "--count", "v0.0.1..HEAD"
                    ).stdout.strip()
                )
                found = self._shallowest_depth_that_describes(Path(tmp), origin)
                self.assertEqual(
                    found,
                    self._shortest_path_length(origin),
                    "the boundary stopped following the shortest path once a "
                    "merge was in the range, which is what the docstring in "
                    "range_start claims it does",
                )
                self.assertNotEqual(
                    found,
                    count + 1,
                    "the boundary matched (commits since the tag) + 1 even "
                    "with a merge in the range, which would mean the simpler "
                    "formula was right and this fixture no longer separates "
                    "the two",
                )

    def test_the_walk_boundary_can_exceed_the_describe_boundary(self):
        """Between the two depths the gate publishes the wrong version number.

        This module reads the range twice. `git diff start..HEAD` compares two
        trees and needs only the tagged commit; `git log start..HEAD` must
        visit every commit in the range and needs the farthest one. A shallow
        clone can satisfy the first and not the second.

        The consequence is worse than the untagged case, not milder. That one
        claims every tracked file and is obvious. This one produces the correct
        file list -- so the release looks entirely normal -- while the subject
        list is short by exactly the commits on the long path. A `feat:` there
        is grafted away and a minor shipped as a patch.

        The docstring in range_start once said the answer above the describe
        boundary was byte-identical to a full clone. It is not; byte-identity
        starts at the walk boundary, and these two are the numbers that show it.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._asymmetric_origin(Path(tmp))
            describe_at = self._shallowest_depth_that_describes(Path(tmp), origin)
            walk_at = self._walk_boundary(Path(tmp), origin)

            self.assertLess(
                describe_at,
                walk_at,
                "this fixture no longer separates the two boundaries, so it "
                "cannot show the failure it exists to show -- the tag has "
                "probably stopped being reachable by a shortcut",
            )

            shallow = Path(tmp) / "at_describe"
            self._run(
                Path(tmp),
                "clone",
                "-q",
                "--depth",
                str(describe_at),
                origin.as_uri(),
                str(shallow),
            )
            self._run(shallow, "fetch", "--tags", "-q")

            # The file list is already correct here. That is what makes this
            # failure quiet: nothing about the diff looks wrong.
            self.assertEqual(
                self._run(
                    shallow, "diff", "--name-only", "v0.0.1..HEAD"
                ).stdout.split(),
                self._run(
                    origin, "diff", "--name-only", "v0.0.1..HEAD"
                ).stdout.split(),
                "the diff already disagreed at the describe boundary, which "
                "would make this the loud failure rather than the quiet one",
            )

            truth = self._subjects(origin)
            seen = self._subjects(shallow)
            self.assertNotEqual(
                seen,
                truth,
                "the subject list was already complete at the describe "
                "boundary, so on this history the two boundaries coincide "
                "after all and the docstring's older claim was right",
            )
            self.assertEqual(
                release_decision.bump_from_subjects(truth),
                "minor",
                "the fixture stopped containing a feat: in the range, so it "
                "can no longer show a bump being downgraded",
            )
            self.assertEqual(
                release_decision.bump_from_subjects(seen),
                "patch",
                "the truncated walk did not change the bump, which is the "
                "whole consequence this test exists to pin",
            )

            deep = Path(tmp) / "at_walk"
            self._run(
                Path(tmp),
                "clone",
                "-q",
                "--depth",
                str(walk_at),
                origin.as_uri(),
                str(deep),
            )
            self._run(deep, "fetch", "--tags", "-q")
            self.assertEqual(
                self._subjects(deep),
                truth,
                "the walk boundary did not actually reproduce the full walk",
            )

    def test_the_range_size_bounds_the_walk_boundary(self):
        """A number a reader can act on without computing path lengths.

        The walk boundary needs a graph walk to compute, which is not a thing
        anyone is going to do before setting `fetch-depth`. This bound does not:
        every commit on a shortest path to a range commit is itself in the
        range, because if an intermediate one were an ancestor of the tag then
        the target would be too and it would not be in the range. So the
        distance cannot exceed the range size, counting merges.

        The counting matters and is the reason this test enumerates shapes
        rather than stating a sentence. The size this module *reports* is
        `--no-merges`, and that one is not a bound at all -- see the test
        below, which pins the shape that breaks it.
        """
        for name, build in (
            ("linear", lambda t: self._linear_origin(t, 5)),
            ("merged", self._merged_origin),
            ("asymmetric", self._asymmetric_origin),
            ("catchup", self._catchup_merge_origin),
        ):
            with self.subTest(shape=name):
                with tempfile.TemporaryDirectory() as tmp:
                    origin = build(Path(tmp))
                    walk_at = self._walk_boundary(Path(tmp), origin)
                    including = len(
                        [
                            line
                            for line in self._run(
                                origin, "rev-list", "v0.0.1..HEAD"
                            ).stdout.split("\n")
                            if line.strip()
                        ]
                    )
                    self.assertGreaterEqual(
                        including + 1,
                        walk_at,
                        "the range size counting merges stopped bounding the "
                        "walk boundary, which would refute the argument in "
                        "range_start's docstring",
                    )

    def test_the_no_merges_count_is_not_a_bound(self):
        """The claim this suite used to make, pinned as false.

        An earlier version asserted (--no-merges count) + 1 >= walk boundary
        and described it as measurably tight. It is not tight, it is wrong, and
        the shape that breaks it is ordinary: a branch forked before the tag
        catching up by merging the upstream branches in one at a time. Three
        merges, one real commit, off by two.

        The reason the earlier measurement looked tight is the reason this is
        asserted in the failing direction rather than deleted: the evidence for
        calling it tight lived in a message and was never enrolled here, so
        nothing could contradict it. Asserting the failure means reinstating
        the claim turns this red.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._catchup_merge_origin(Path(tmp))
            walk_at = self._walk_boundary(Path(tmp), origin)
            no_merges = len(self._subjects(origin))
            self.assertLess(
                no_merges + 1,
                walk_at,
                "the --no-merges count bounded the walk boundary on the shape "
                "built to break it, so either the fixture stopped having the "
                "catch-up structure or the bound is sound after all",
            )
            # Non-vacuity: the provable bound still holds on this same shape,
            # so the failure above is about which commits are counted rather
            # than the argument being wrong.
            including = len(
                [
                    line
                    for line in self._run(
                        origin, "rev-list", "v0.0.1..HEAD"
                    ).stdout.split("\n")
                    if line.strip()
                ]
            )
            self.assertGreaterEqual(including + 1, walk_at)

    def test_a_grafted_merge_is_not_a_merge_to_git_log(self):
        """Why the count cannot see the boundary it would be used to bound.

        A shallow clone rewrites its boundary commits to have no parents. A
        merge sitting on that boundary therefore is not a merge as far as
        `git log --no-merges` is concerned, and the filter includes it -- a
        commit the same query excludes in a full clone.

        So `--no-merges` is unsound in both directions at once: it drops real
        commits past the boundary and adopts merges at it. On this shape the
        two cancel, and the count reads 1 at every depth, correct and incorrect
        alike, while the subject identities change underneath it. That is why
        _walk_boundary compares subject lists rather than lengths, and why the
        docstring says the observable is the list.
        """
        with tempfile.TemporaryDirectory() as tmp:
            origin = self._catchup_merge_origin(Path(tmp))
            shallow = Path(tmp) / "shallow"
            self._run(
                Path(tmp), "clone", "-q", "--depth", "2", origin.as_uri(), str(shallow)
            )
            self._run(shallow, "fetch", "--tags", "-q")

            boundary = self._run(shallow, "rev-parse", "HEAD^").stdout.strip()
            self.assertEqual(
                len(self._run(origin, "rev-list", "--parents", "-1", boundary).stdout.split())
                - 1,
                2,
                "the commit on the graft boundary is not a merge upstream, so "
                "this fixture cannot show the filter adopting one",
            )
            self.assertEqual(
                len(
                    self._run(
                        shallow, "rev-list", "--parents", "-1", boundary
                    ).stdout.split()
                )
                - 1,
                0,
                "the boundary commit kept its parents in the shallow clone, so "
                "grafting did not happen and the mechanism described in "
                "range_start's docstring is not real",
            )

            upstream = self._run(
                origin, "rev-list", "v0.0.1..HEAD", "--no-merges"
            ).stdout
            local = self._run(
                shallow, "rev-list", "v0.0.1..HEAD", "--no-merges"
            ).stdout
            self.assertNotIn(
                boundary,
                upstream,
                "--no-merges included the merge in the full clone, so there is "
                "no disagreement left to demonstrate",
            )
            self.assertIn(
                boundary,
                local,
                "--no-merges excluded the grafted merge, which would mean the "
                "filter is depth-stable after all",
            )

            # The count is the same on both sides. Only the identities differ,
            # which is the whole point: a length cannot see this.
            self.assertEqual(
                len(local.split()),
                len(upstream.split()),
                "the counts differed, which would make this visible to a "
                "length comparison and the docstring's warning unnecessary",
            )

    def test_the_refusal_says_what_to_do_about_it(self):
        try:
            release_decision.range_start("", True)
        except release_decision.ShallowCheckoutError as err:
            message = str(err)
        else:
            self.fail("the guard did not fire")
        self.assertTrue(
            "fetch-depth: 0" in message,
            "the refusal does not name the fix, so whoever hits it in CI has "
            "to come and read this module:\n" + message,
        )


class WorkflowWiringTests(unittest.TestCase):
    """A correct decision that nothing calls is not a fix."""

    def test_the_workflow_has_exactly_one_decider(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        # assertIn would print the whole workflow file on failure, which makes
        # the failure unreadable and therefore unread. Assert the boolean and
        # say the one thing worth knowing.
        self.assertTrue(
            "release_decision.py" in workflow,
            "the release workflow does not invoke the decision module, so the "
            "module is dead code and something else is still deciding",
        )
        stale = [
            line.strip()
            for line in workflow.splitlines()
            if 'BUMP="' in line or "BUMP=$" in line
        ]
        self.assertFalse(
            stale,
            "the inline bash bump logic is still present, so there are two "
            "deciders and the pipeline consults the wrong one:\n    %s"
            % "\n    ".join(stale),
        )

    def test_every_job_that_reads_history_checks_out_all_of_it(self):
        """The suite's fixture and the gate's input are both git history.

        The changelog tests replay every tag-to-tag range, and `collect()`
        resolves the range from tags. A default `actions/checkout` is shallow
        and has neither, and the two consumers fail in opposite directions:
        the tests go red, and the release gate publishes.

        An earlier version of this test named `validate.yml` and stopped there,
        which asserted one consumer of a rule that has two. The jobs are
        discovered instead, so a third one added later is covered by the same
        assertion rather than by remembering.

        Two blind spots remain and are worth stating rather than implying.
        Actions accepts `.yaml` as readily as `.yml`, so both are globbed. And
        the markers below are invocation strings: a job that ran the suite as
        `pytest` would read history and be invisible here. That is the same
        shape as naming a file, one level in, and it is not fully solvable from
        inside a workflow -- nothing in the YAML declares "this job reads git
        history". The must-find assertion is the compensating control: if the
        markers ever stop matching, the count drops and this goes red rather
        than passing over an empty set.
        """
        needs_history = ("unittest discover", "release_decision.py")
        offenders = []
        checked = []
        workflows = sorted(
            path
            for pattern in ("*.yml", "*.yaml")
            for path in (ROOT / ".github" / "workflows").glob(pattern)
        )
        self.assertTrue(
            workflows,
            "no workflow files were found at all, so this test is asserting "
            "nothing -- check the glob before trusting a green run",
        )
        for path in workflows:
            text = path.read_text(encoding="utf-8")
            for job in re.split(r"\n(?=  \w[\w-]*:\n)", text):
                if not any(marker in job for marker in needs_history):
                    continue
                name = job.strip().splitlines()[0].rstrip(":")
                checked.append(f"{path.name}:{name}")
                if "fetch-depth: 0" not in job:
                    offenders.append(f"{path.name}:{name}")
        self.assertGreaterEqual(
            len(checked),
            2,
            "expected at least the test job and the release job to read "
            "history, found %s" % checked,
        )
        self.assertTrue(
            not offenders,
            "these jobs read git history but check out shallowly, so the "
            "tests will see an empty fixture and the release gate will treat "
            "every tracked file as new: %s" % ", ".join(offenders),
        )

    def test_the_release_body_compares_two_tags(self):
        """The published link must span the release, not start at it.

        Every release so far linked `compare/<this tag>...main`. On the day it
        is cut those are the same commit, so the link is empty; afterwards it
        shows the work that came next. It never once showed what was in the
        release it was attached to.
        """
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        compare = [
            line.strip() for line in workflow.splitlines() if "/compare/" in line
        ]
        self.assertEqual(len(compare), 1, "expected exactly one comparison link")
        link = compare[0]
        self.assertFalse(
            link.endswith("main"),
            "the release body compares the new tag against main, which is the "
            "same commit at publication time and a growing list of later work "
            "afterwards:\n    " + link,
        )
        self.assertTrue(
            "previous_tag" in link,
            "the comparison does not start at the previous tag, so it cannot "
            "describe this release:\n    " + link,
        )

    def test_every_output_the_workflow_reads_is_one_the_module_writes(self):
        """A template referencing an output nobody sets renders as empty.

        GitHub Actions does not fail on an unknown `steps.*.outputs.*`; it
        substitutes nothing. So the failure mode for a typo here is a release
        note with a hole in it, which nobody sees until it is published.
        """
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        source = (ROOT / "scripts" / "release_decision.py").read_text(
            encoding="utf-8"
        )
        read = set(re.findall(r"steps\.bump\.outputs\.([A-Za-z_]+)", workflow))
        written = set(re.findall(r'handle\.write\(f?"([a-z_]+)[=<]', source))
        self.assertTrue(read, "the workflow reads no outputs from the decider")
        missing = sorted(read - written)
        self.assertTrue(
            not missing,
            "the workflow reads decider outputs that the module never writes, "
            "so they render as empty strings: %s" % ", ".join(missing),
        )


if __name__ == "__main__":
    unittest.main()
