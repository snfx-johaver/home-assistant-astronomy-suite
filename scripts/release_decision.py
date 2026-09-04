#!/usr/bin/env python3
"""Decide whether a push to main should cut a release.

WHY THIS IS A MODULE AND NOT SIX LINES OF BASH

It used to be six lines of bash inlined in `.github/workflows/release.yml`,
and it was wrong for at least three releases without anyone noticing. Bash in
a `run:` block is unreachable from the test suite, so the only way to find out
what it decides is to merge something and watch. That is a slow, public and
irreversible test: a wrong answer is a published GitHub release and a version
number HACS offers to every user.

The decision is now a pure function of two lists -- commit subjects and changed
paths -- with no git, no network and no environment. `main()` collects those two
lists and does the I/O. Everything worth being wrong about is in `decide()`,
which a unit test can call directly.

THE DEFECT THIS EXISTS TO FIX

The old rule decided "is this release-worthy?" from the commit subject prefix
alone. `fix:` meant a patch release. That is a claim about the *author's intent*,
and it was standing in for a claim about the *diff*:

    v1.11.7  <- PR #15, diff was tests/test_version_literals.py, nothing else
    v1.11.8  <- PR #17, diff was tests/harness.py + tests/, nothing else

Both were honestly typed. `fix:` is the correct conventional-commit type for
fixing a defect in a test harness -- the author was not being careless, and
renaming the commit would have been a lie. The prefix was simply never evidence
for the question being asked of it.

So there were two deciders of "does this reach a user": the commit type, which
the pipeline consulted, and the set of changed paths, which actually determined
it and which the pipeline never looked at. This module makes the second one
speak, and requires both to agree before a release is cut.

WHY THE SHIPPING SET IS DERIVED AND THE EXEMPTIONS ARE DECLARED

An earlier version of this module hand-wrote both maps, on the stated grounds
that "there is no artefact here that states what ships". That was false, and
it was false in the same shape as the defect above: the hand-written map was
consulted, while two artefacts that actually determine the answer were never
asked.

    HACS installs the directory containing `manifest.json`, and nothing else.
    `custom_components/nasa_astronomy/__init__.py::_deploy_cards_to_www` copies
    the card bundles into the user's `config/www/` from `Path(__file__).parent`
    -- the *installed package* directory.

So the browser-facing bundles reach a browser from inside `custom_components/`.
The repository's top-level `www/` copies are byte-identical duplicates that
nothing builds and nothing reads; they were classified as shipping because they
look like product. They were the deciding vote exactly once in this
repository's history, and that once published v1.11.6, which reached no
installation.

Four more entries were wrong for related reasons: `lovelace/` is an example a
user copies by hand, `info.md` is not rendered by HACS 2.x at all, and the root
`icon.png` / `logo.png` are referenced by nothing -- the brand images HACS uses
live inside the package.

The positive set is therefore computed from those two artefacts. What stays
hand-written is only the list of paths that ship *nothing*, where being wrong
withholds a release rather than publishing an empty one, and where a mistake is
caught by `test_nothing_that_ships_is_declared_not_shipping`.

WHY `README.md` COUNTS AS SHIPPING

It looks like documentation, so it is worth stating the mechanism. HACS fetches
the rendered README from the ref of the version it is showing --
`HacsRepository.get_documentation` in hacs/integration resolves that to the
installed version for an installed repository, and to the latest release tag
otherwise. It never reads the default branch. So a README change on `main`
reaches nobody until a release is cut, which is exactly the test this module
applies to everything else.

Which file it renders comes from a hardcoded list of README spellings, not from
`hacs.json`. An earlier version of this module gated the README on the
`render_readme` key, which is still accepted by HACS's schema and no longer
consulted by its renderer -- the same defect again, this time inside the fix
for it: turning that key off would have silently stopped documentation
releasing while every user carried on seeing the change. It is also why
`info.md` renders nowhere however it is configured.

"REACHES A USER ONLY VIA A RELEASE" IS NOT ONE PROPERTY

The two non-code entries in the derived set both satisfy the rule this module
applies, and they satisfy it on different schedules. This cannot be asserted by
a test here -- it is a fact about HACS's source, not about this repository --
so it is recorded where the next person will meet it.

    README.md   get_documentation()   -> installed_version when installed
    hacs.json   async_get_hacs_json() -> version_to_download(), which has no
                                         `installed` branch at all

A README change reaches a user when *that user upgrades*. A `hacs.json` change
reaches every existing installation the moment a release is cut, whether or not
anyone upgrades, because HACS resolves it against the newest published tag.

The practical consequence is the `homeassistant` minimum. Raising it does not
merely gate new installs: cutting any release afterwards applies the new floor
to users still sitting on an older version who never asked for anything. That
is not a defect and there is nothing here to fix, but it is worth knowing
before that number is moved.

DECLARED LIMITS

Two things this cannot see. Both are stated here so the next person meets the
boundary instead of trusting the coverage:

1. Classification is top-level only. `custom_components/` ships, so a
   hypothetical `custom_components/notes/` would be classified as shipping
   without anyone deciding that. The error direction is a release that need not
   have happened, which is the behaviour that existed before this module and is
   the safe way round. A subdirectory-granular map would be more precise and
   would also be a longer hand-maintained list; that trade is not obviously
   worth making yet.

2. It reasons about paths, not content. A whitespace-only edit to a shipped
   file releases, and a change that alters behaviour without touching a
   classified path -- a dependency pinned in CI, say -- does not. Path is a
   proxy for "can a user see this", and a good one here only because this
   repository vendors everything it ships.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, NamedTuple

ROOT = Path(__file__).resolve().parent.parent

# The spellings HACS will render, in the order it tries them. Taken from
# `HacsRepository.get_info_md_content` in hacs/integration, where the list is
# built from a hardcoded `name: str = "readme"` -- not from `render_readme`,
# which its schema still accepts and its renderer no longer consults.
README_VARIANTS: tuple[str, ...] = (
    "README.md",
    "readme.md",
    "readme.MD",
    "README.MD",
    "README",
    "readme",
)

# Top-level paths that cannot reach a user's installation. Hand-written,
# unlike SHIPPING, because "this ships nothing" is not derivable -- but a wrong
# entry here withholds a release rather than publishing an empty one, and
# `test_nothing_that_ships_is_declared_not_shipping` catches it either way.
# The value is why, because an entry that cannot say why it is exempt is an
# entry nobody can review.
NOT_SHIPPING: dict[str, str] = {
    "tests": "never installed; runs only in CI and on a developer's machine",
    ".github": "CI configuration; runs in Actions, ships nothing",
    "scripts": (
        "release tooling. A change here cannot reach a user except by being "
        "run during some later release, which will deliver it then. Cutting a "
        "release because the release script changed is circular."
    ),
    "www": (
        "byte-identical duplicates of the bundles inside the package, plus "
        "TypeScript sources and a rollup config that nothing in CI builds. "
        "The integration deploys cards from its own installed directory, so "
        "these copies are read by nobody. When a bundle genuinely changes, "
        "custom_components/ is in the diff and already permits the release."
    ),
    "lovelace": (
        "an example dashboard a user copies by hand from the README. Nothing "
        "installs it, so changing it changes no existing installation."
    ),
    "info.md": (
        "unsupported since HACS 2.0, which always renders README.md. Kept in "
        "the tree for older forks; rendered to nobody by this repository."
    ),
    "icon.png": (
        "referenced by nothing. The brand images HACS and Home Assistant use "
        "are inside the package, at custom_components/nasa_astronomy/brand/."
    ),
    "logo.png": (
        "referenced by nothing; see icon.png. Both are repository decoration."
    ),
    "CONTRIBUTING.md": "instructions for contributors, not for users",
    "LICENSE": "not installed by HACS into the user's config",
    ".gitignore": "git metadata",
    "version.json": (
        "written by the release itself. It is the record of a release, never "
        "the reason for one."
    ),
}


class Decision(NamedTuple):
    """The answer, plus the reason, because a bare bool cannot be audited."""

    release: bool
    bump: str  # "major" | "minor" | "patch" | "none"
    reason: str


class Commit(NamedTuple):
    """One commit's subject and the paths it touched.

    `decide()` deliberately does not see this. The gate reads the range as a
    whole -- `git diff LAST_TAG..HEAD` -- because a file added in one commit
    and removed in the next changed nothing, and the release question is about
    the net effect. The release *notes* are a different question, asked per
    commit, and answering it needs the association this type carries.
    """

    subject: str
    paths: tuple[str, ...]


def top_level(path: str) -> str:
    """The first path segment, which is the granularity the maps classify at."""
    return path.split("/", 1)[0]


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return [p for p in out.splitlines() if p.strip()]


def installed_roots() -> dict[str, str]:
    """Top-level paths HACS copies into a user's configuration.

    HACS installs an integration from the directory containing `manifest.json`.
    That directory is discovered here rather than named, so the answer comes
    from the repository rather than from someone's memory of its layout.
    """
    roots = {}
    for path in _tracked():
        if Path(path).name == "manifest.json":
            roots[top_level(path)] = (
                f"HACS installs the integration at {Path(path).parent.as_posix()}, "
                "discovered by its manifest.json"
            )
    return roots


def displayed_roots(tracked: Iterable[str] | None = None) -> dict[str, str]:
    """Top-level paths HACS renders, for an installed and for a browsing user.

    Nothing here reads the *content* of `hacs.json`. An earlier version gated
    the README on its `render_readme` key, which reproduced this module's own
    defect: HACS's renderer picks from a hardcoded list of README spellings and
    has not consulted that key for some time, so a repository could switch it
    off and silently stop releasing its documentation while every user kept
    seeing the change.

    `hacs.json` is matched at the repository root exactly. There is a second
    one nested under `www/`, describing a Lovelace plugin this repository does
    not publish as one; matching the exact path rather than the filename is the
    difference between reading the configuration and finding a file with the
    right name.

    `tracked` exists so a test can ask what this would decide about a
    repository other than the one it is standing in.
    """
    if tracked is None:
        tracked = _tracked()
    tracked = set(tracked)

    roots = {}
    if "hacs.json" in tracked:
        roots["hacs.json"] = (
            "governs how HACS installs this repository, read at the version it "
            "would download -- so a change reaches nobody until a release is "
            "cut, and then reaches everybody at once. Unlike the README, it "
            "does not follow the user's installed version."
        )
    for name in README_VARIANTS:
        if name in tracked:
            roots[name] = (
                "HACS renders it in the store listing, and fetches it from the "
                "ref of the version being shown -- the installed version for an "
                "installed repository, otherwise the latest release tag. It "
                "never reads the default branch, so a change here reaches no "
                "user until a release is cut."
            )
            break
    return roots


def derived_shipping() -> dict[str, str]:
    """What can actually reach a user: installed, or displayed by HACS."""
    return {**installed_roots(), **displayed_roots()}


# Computed once, so `decide()` stays a pure function of its two arguments and
# a unit test can call it without touching a repository.
SHIPPING: dict[str, str] = derived_shipping()


def bump_from_subjects(subjects: Iterable[str]) -> str:
    """Conventional-commit type -> bump size.

    Deliberately a faithful port of the bash it replaces, including its
    looseness: `^.*!:` matches a `!:` anywhere on the line and `BREAKING.CHANGE`
    is unanchored with `.` still a wildcard. Porting the rule and fixing it in
    the same change would have made the must-fail control ambiguous about which
    edit caused which result.
    """
    lines = [s for s in subjects if s.strip()]
    if any(re.search(r"^.*!:|BREAKING.CHANGE", s, re.IGNORECASE) for s in lines):
        return "major"
    if any(re.search(r"^feat", s, re.IGNORECASE) for s in lines):
        return "minor"
    if any(re.search(r"^fix|^perf|^refactor", s, re.IGNORECASE) for s in lines):
        return "patch"
    return "none"


def ships(changed_paths: Iterable[str]) -> list[str]:
    """The subset of the diff that can reach a user's installation."""
    return sorted({p for p in changed_paths if top_level(p) in SHIPPING})


def decide(subjects: Iterable[str], changed_paths: Iterable[str]) -> Decision:
    """Whether this push should cut a release.

    Both deciders must agree. The commit type sizes the bump and is the
    author's claim about intent; the diff decides whether anything reaches a
    user and is a fact about the change. Requiring both means an honestly
    typed `fix:` against a test cannot ship a version number, without anyone
    having to remember to type it differently.
    """
    subjects = list(subjects)
    if not [s for s in subjects if s.strip()]:
        return Decision(False, "none", "no commits since the last tag")

    bump = bump_from_subjects(subjects)
    if bump == "none":
        return Decision(False, "none", "no commit type implies a version bump")

    shipped = ships(changed_paths)
    if not shipped:
        return Decision(
            False,
            "none",
            "a %s bump was implied, but nothing in the diff reaches an "
            "installation" % bump,
        )

    return Decision(
        True, bump, f"a {bump} bump, and {len(shipped)} shipped file(s) changed"
    )


def changelog(commits: Iterable[Commit]) -> str:
    """The release-notes body, partitioned by whether a commit reaches a user.

    This module already knows which paths reach an installation, and until now
    it applied that knowledge to *whether* to release and not to *what it said*
    when it did. The result was release notes headed "What's Changed" listing
    changes that, by this module's own definition, changed nothing for the
    reader. v1.11.8 is the worked example: both of its commits touched only
    `tests/`, so its entire changelog described work no user received.

    The answer is to partition rather than to filter. Dropping the internal
    commits would make the notes an incomplete record of the tag, and silently
    discarding things you have classified is the exact defect this repository
    removed from the version sweep. Every commit appears exactly once; the
    heading says which of the two it is.
    """
    commits = list(commits)
    shipped = [c for c in commits if ships(c.paths)]
    internal = [c for c in commits if not ships(c.paths)]

    if shipped:
        lines = [f"- {c.subject}" for c in shipped]
    else:
        # Only reachable on a SKIP, where nothing renders this. Total anyway,
        # because a function that is correct only for its callers is a trap.
        lines = ["_Nothing in this release reaches an installation._"]

    if internal:
        lines += [
            "",
            "### Also in this release",
            "",
            "These changed the repository without changing the integration "
            "HACS installs, so they reach no configuration.",
            "",
        ]
        lines += [f"- {c.subject}" for c in internal]

    return "\n".join(lines)


class ShallowCheckoutError(RuntimeError):
    """The range cannot be determined because the history is not all here."""


def range_start(last_tag: str, is_shallow: bool) -> str | None:
    """Where the range begins, or None meaning "everything tracked".

    `git describe` fails identically for two different worlds: a repository
    that has never been tagged, and a repository where the last tagged commit
    is outside the shallow history. The first is a genuine first release and
    `ls-files` is the right answer for it. The second turns the gate into an
    unconditional publish, claiming every tracked file as new.

    The mechanism is commit reachability, not whether tag refs were fetched.
    A shallow clone of this repository followed by `git fetch --tags` has
    every tag present as a ref and `describe` still exits 128, because it
    walks ancestors from HEAD and the graft boundary is in the way. So "the
    tags are here" is not a safe proxy for "the range is computable", and the
    tag list is not what this function is allowed to look at.

    The refusal covers the whole shallow space rather than only the untagged
    corner, and the reason is that a bounded depth is not wrong -- it is
    *contingently* right, on a contingency that moves. There are two depths
    here, not one, because this module reads the range twice and the two reads
    ask different questions:

        `git diff start..HEAD` compares two trees, so it needs only that the
        tagged commit is reachable. That depth -- call it the describe
        boundary -- is the number of commits on the shortest path from HEAD to
        the last tagged commit, counting both ends.

        `git log start..HEAD` must visit every commit in the range, so it
        needs the *farthest* of them present. That depth -- the walk boundary
        -- is the greatest distance from HEAD to anything in the range.

    The walk boundary is the larger of the two and it is the one a reader
    needs, because the file list decides *whether* to release and the subjects
    decide *which bump*. Between the two depths the file list is already
    correct while the subject list is still short, so the gate publishes a
    plausible release carrying the wrong version number -- a `feat:` sitting
    on a long path is grafted away and a minor is published as a patch. That
    is harder to notice than the untagged case, which claims every tracked
    file at once.

    They coincide whenever the tagged commit is the farthest thing in the
    range, which is why linear history and most merge shapes do not show the
    difference. A branch cut at the tag and merged after the mainline moved on
    separates them: the tag gets a shortcut while the mainline stays long.

    On linear history both are (commits since the tag) + 1. Neither is that in
    general. A sound upper bound over both is (commits in the range *counting
    merges*) + 1, because every commit on a shortest path to a range commit is
    itself in the range -- if an intermediate one were an ancestor of the tag
    the target would be too, and it would not be in the range. Note the
    counting: the range size this module reports is `--no-merges`, and that
    one is measurably tight rather than provably sound. All of this is pinned
    by tests.

    Below the describe boundary the gate does not degrade, it inverts: every
    tracked file is claimed as changed. At or above the walk boundary the
    answer is byte-identical to a full clone. So any fixed `fetch-depth: N` is
    correct only while the longest path stays under N, and it lengthens with
    every commit and resets only when a release is cut -- which is the event
    this module exists to suppress. The better this gate works, the faster
    someone else's bounded depth expires. That is the drift this module
    removes, so the contingent cases are refused too, including the ones that
    would have been correct.

    The boundary is described rather than illustrated on purpose. An earlier
    version of this docstring carried a table of measured depths against a
    named tag; it was accurate when written and began decaying immediately,
    because the boundary it described moves. The numbers live in the tests,
    where they are re-derived and can go red. See ShallowCheckoutTests.

    What this deliberately does NOT claim: that a bounded depth produces a
    wrong range. It does not. If `describe` succeeds the tag is reachable and
    the range walks correctly, merges included. That is pinned by a test, so
    nobody re-derives the stronger and false version of this argument.
    """
    if is_shallow:
        raise ShallowCheckoutError(
            "this is a shallow clone, so a failed `git describe` cannot be "
            "distinguished from a genuine first release -- the tagged commit "
            "may simply be past the graft boundary, which fetching the tags "
            "does not fix. Refusing to guess: treating it as a first release "
            "would claim every tracked file as new and publish "
            "unconditionally. Check out with fetch-depth: 0."
        )
    return last_tag or None


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


_RECORD = "\x1e"  # cannot occur in a commit subject


def _parse_log(raw: str) -> list[Commit]:
    """Split `git log --name-only` output into commits.

    Kept separate from the subprocess call so the parsing can be tested against
    recorded output instead of only against whatever this repository happens to
    contain today.
    """
    commits = []
    for chunk in raw.split(_RECORD):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        commits.append(Commit(lines[0], tuple(lines[1:])))
    return commits


def _repo_is_shallow() -> bool:
    return _git("rev-parse", "--is-shallow-repository").strip() == "true"


def collect() -> tuple[list[Commit], list[str], str]:
    """Read the range out of git. The only impure part of this module."""
    try:
        last_tag = _git("describe", "--tags", "--abbrev=0").strip()
    except subprocess.CalledProcessError:
        last_tag = ""

    start = range_start(last_tag, _repo_is_shallow())

    rev_range = f"{start}..HEAD" if start else "HEAD"
    commits = _parse_log(
        _git(
            "log",
            rev_range,
            f"--pretty=format:{_RECORD}%s",
            "--name-only",
            "--no-merges",
        )
    )
    if start:
        paths = _git("diff", "--name-only", f"{start}..HEAD").splitlines()
    else:
        paths = _git("ls-files").splitlines()
    return commits, [p for p in paths if p.strip()], last_tag


def main() -> int:
    commits, paths, last_tag = collect()
    subjects = [c.subject for c in commits]
    decision = decide(subjects, paths)

    print(f"decision: {'RELEASE' if decision.release else 'SKIP'} ({decision.bump})")
    print(f"reason:   {decision.reason}")
    print(f"commits:  {len(subjects)}")
    print(f"changed:  {len(paths)} file(s), {len(ships(paths))} of them shipped")

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        # The changelog is emitted here rather than recomputed in bash so that
        # the range is resolved exactly once. Two independent walks of
        # LAST_TAG..HEAD is the same defect this module exists to remove.
        #
        # `previous_tag` goes out for the same reason. The release body links a
        # comparison, and the only honest endpoints for it are the tag before
        # this release and the tag being cut. The workflow cannot name the
        # first without re-deriving it, so it is published here instead.
        body = changelog(commits)
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"skip={'false' if decision.release else 'true'}\n")
            handle.write(f"bump={decision.bump}\n")
            handle.write(f"reason={decision.reason}\n")
            handle.write(f"previous_tag={last_tag}\n")
            handle.write(f"changelog<<RELEASE_DECISION_EOF\n{body}\n")
            handle.write("RELEASE_DECISION_EOF\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
