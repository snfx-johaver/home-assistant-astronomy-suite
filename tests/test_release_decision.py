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
        deployed = [
            package_init.CARDS_FILENAME,
            package_init.DEEPSKY_CARDS_FILENAME,
            "world-map.png",
        ]
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
