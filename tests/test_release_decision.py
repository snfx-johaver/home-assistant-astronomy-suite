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

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import release_decision  # noqa: E402
from release_decision import (  # noqa: E402
    NOT_SHIPPING,
    SHIPPING,
    bump_from_subjects,
    decide,
    top_level,
)


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


if __name__ == "__main__":
    unittest.main()
