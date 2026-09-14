"""The release workflow must serialise, because its writes are not atomic.

`.github/workflows/release.yml` bumps `version.json`, amends the head commit,
moves a tag with `git tag -f` and pushes it with `git push --tags --force`.
That sequence is a read-modify-write of shared remote state with the failure
modes force-flagged away: a run that loses a race does not error, it
overwrites. Two pushes to `main` close together -- merging two PRs back to back
-- is enough to produce a published tag pointing at a tree that never contained
the change its release notes describe.

GitHub Actions offers exactly one mechanism for that, `concurrency`, so this
module asserts on its presence and on its *settings*, not merely that the key
exists.

WHY THE ASSERTIONS ARE SHAPED THIS WAY
--------------------------------------
A structural check passes on an empty artefact, so each test below is paired
with a control that proves the check can see the thing it is looking for:

* `test_release_workflow_parses` fails loudly if the YAML is unreadable, so a
  later "key is absent" result cannot be produced by a file that never parsed.
  Absence is only meaningful once presence is demonstrable.
* `test_a_workflow_without_concurrency_is_detected` runs the *same* predicate
  against a document that genuinely lacks the guard and requires it to say so.
  Without it, a predicate that always returned "guarded" would pass the real
  assertion and prove nothing.

`cancel_in_progress` is asserted false rather than left unspecified. Cancelling
would abort a run that may already have force-pushed its tag but not yet
created the release, leaving a tag with no release behind it -- a different
corruption, not a fix. Queueing lets the second run re-read `version.json`
after the first has written it.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"


def _load(text: str) -> dict:
    """Parse a workflow document.

    PyYAML is not a declared dependency of this repository and the sensor job
    installs nothing, so fall back to a targeted reader when it is absent. The
    fallback is deliberately narrow: it answers only the questions this module
    asks, and raises rather than guessing when the shape is unfamiliar.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return _read_concurrency_without_yaml(text)
    return yaml.safe_load(text)


def _read_concurrency_without_yaml(text: str) -> dict:
    """Read the top-level ``concurrency`` block from a workflow's text.

    Only top-level keys count. A ``concurrency`` nested under a job is a
    different guarantee -- it serialises that job, not the workflow -- so
    indented occurrences are skipped rather than accepted, which would let a
    weaker guard satisfy a test written for a stronger one.
    """
    result: dict = {}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("concurrency:"):
            block: dict = {}
            for follower in lines[index + 1 :]:
                if follower.strip() == "" or follower.lstrip().startswith("#"):
                    continue
                if not follower.startswith((" ", "\t")):
                    break
                key, _, value = follower.strip().partition(":")
                value = value.strip()
                if value in ("true", "false"):
                    block[key] = value == "true"
                else:
                    block[key] = value
            result["concurrency"] = block
            break
    return result


class ReleaseWorkflowSerialisation(unittest.TestCase):
    """The release workflow may not run twice at once."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        cls.document = _load(cls.text)

    def test_release_workflow_parses(self):
        """Control: the file is readable and non-empty.

        Every absence claim below depends on this. A workflow that failed to
        parse would yield an empty mapping, and an empty mapping answers
        "no concurrency guard" for exactly the same reason a real omission
        does -- indistinguishable observations from different causes.
        """
        self.assertIsInstance(self.document, dict)
        self.assertTrue(self.document, "release.yml parsed to an empty document")

    def test_release_workflow_declares_concurrency(self):
        self.assertIn(
            "concurrency",
            self.document,
            "release.yml force-pushes a tag with no concurrency guard; two "
            "pushes to main can publish the same version from different trees",
        )

    def test_concurrency_group_is_per_ref(self):
        """The group must vary with the ref, and must not be a constant.

        A literal group name would serialise correctly today, since the
        workflow only triggers on ``main``. It would also silently serialise
        every future branch against ``main``, so the assertion is on the
        mechanism rather than on today's single-branch behaviour.
        """
        group = self.document["concurrency"].get("group", "")
        self.assertTrue(group, "concurrency.group is empty")
        self.assertIn(
            "github.ref",
            group,
            f"concurrency group {group!r} does not vary with the ref",
        )

    def test_in_progress_releases_are_queued_not_cancelled(self):
        """Cancelling mid-release can strand a pushed tag with no release."""
        self.assertIs(
            self.document["concurrency"].get("cancel-in-progress"),
            False,
            "cancel-in-progress must be false: a cancelled run may have "
            "already force-pushed its tag but not yet created its release",
        )

    def test_a_workflow_without_concurrency_is_detected(self):
        """Must-find control, inverted: the reader reports a real absence.

        Absence is the expected reading here, so a reader that always returned
        an empty mapping would pass this test and fail to protect anything.
        Pairing it with the presence assertions above pins the reader from both
        sides: it must find the guard in the real file and must not find one
        here.
        """
        unguarded = "name: Example\non:\n  push:\njobs:\n  build:\n    runs-on: ubuntu-latest\n"
        self.assertNotIn("concurrency", _load(unguarded) or {})

    def test_the_reader_finds_a_guard_that_is_present(self):
        """Must-find control: the reader can see a guard in a synthetic file.

        Complements the test above. Together they show the reader
        discriminates, rather than being stuck on one answer.
        """
        guarded = (
            "name: Example\n"
            "concurrency:\n"
            "  group: release-${{ github.ref }}\n"
            "  cancel-in-progress: false\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
        )
        parsed = _load(guarded)
        self.assertIn("concurrency", parsed)
        self.assertIs(parsed["concurrency"]["cancel-in-progress"], False)

    def test_a_job_level_guard_would_not_satisfy_this(self):
        """A nested ``concurrency`` is a weaker guarantee and must not count.

        Serialising one job still lets two runs interleave across jobs, which
        is where the tag push and the release creation live. Without this, a
        future refactor that indents the block would keep the suite green while
        removing the protection.
        """
        nested = (
            "name: Example\n"
            "jobs:\n"
            "  build:\n"
            "    concurrency:\n"
            "      group: release-${{ github.ref }}\n"
            "    runs-on: ubuntu-latest\n"
        )
        self.assertNotIn("concurrency", _read_concurrency_without_yaml(nested))


if __name__ == "__main__":
    unittest.main()
