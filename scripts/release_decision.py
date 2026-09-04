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

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, NamedTuple

ROOT = Path(__file__).resolve().parent.parent

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


def displayed_roots() -> dict[str, str]:
    """Top-level paths HACS renders to a user who has not installed anything.

    Read from the *root* `hacs.json`. There is a second `hacs.json` nested
    under `www/`, which describes a Lovelace plugin that this repository does
    not publish as one; anchoring to the root file explicitly is the difference
    between reading the configuration and finding a file with the right name.
    """
    config = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    roots = {
        "hacs.json": "governs how HACS installs this repository into every install"
    }
    if config.get("render_readme"):
        roots["README.md"] = "hacs.json sets render_readme, so HACS shows it in its UI"
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


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def collect() -> tuple[list[str], list[str]]:
    """Read the two lists out of git. The only impure part of this module."""
    try:
        last_tag = _git("describe", "--tags", "--abbrev=0").strip()
    except subprocess.CalledProcessError:
        last_tag = ""

    rev_range = f"{last_tag}..HEAD" if last_tag else "HEAD"
    subjects = _git(
        "log", rev_range, "--pretty=format:%s", "--no-merges"
    ).splitlines()
    if last_tag:
        paths = _git("diff", "--name-only", f"{last_tag}..HEAD").splitlines()
    else:
        paths = _git("ls-files").splitlines()
    return [s for s in subjects if s.strip()], [p for p in paths if p.strip()]


def main() -> int:
    subjects, paths = collect()
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
        changelog = "\n".join(f"- {s}" for s in subjects)
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"skip={'false' if decision.release else 'true'}\n")
            handle.write(f"bump={decision.bump}\n")
            handle.write(f"reason={decision.reason}\n")
            handle.write(f"changelog<<RELEASE_DECISION_EOF\n{changelog}\n")
            handle.write("RELEASE_DECISION_EOF\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
