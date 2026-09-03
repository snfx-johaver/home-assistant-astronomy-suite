#!/usr/bin/env python3
"""
Version bump script for Home Assistant Astronomy Suite.

Usage:
  python scripts/bump_version.py [major|minor|patch]

Updates version in all files:
  - version.json
  - custom_components/nasa_astronomy/manifest.json
  - www/community/astronomy-cards/package.json
  - astronomy-cards.js in BOTH locations (header comment, VERSION, console banner)

__init__.py is deliberately absent: its VERSION now derives from manifest.json
via const.INTEGRATION_VERSION, so there is no literal left to rewrite and a
rewrite step here would abort every release on its own no-match guard.

The bump runs in two phases. Every step computes its replacements and verifies
each pattern matched, returning the writes it wants rather than performing
them; only once all of them have succeeded is anything written to disk. The
substitution guards exist because a bundle rename once made the patterns stop
matching and the banner drifted silently -- but a guard that fires midway
through writing leaves a half-bumped tree, and the two card bundles are
required to stay byte-identical. Validate-then-write means a release either
happens or doesn't, with no third state.

Then creates a git tag and commit.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERSION_FILES = {
    "version_json": ROOT / "version.json",
    "manifest": ROOT / "custom_components" / "nasa_astronomy" / "manifest.json",
    "package": ROOT / "www" / "community" / "astronomy-cards" / "package.json",
}

# The card bundle ships from two locations that must stay byte-identical
# (see README "Architecture"), so the version banner is rewritten in both.
CARDS_JS_FILES = (
    ROOT / "custom_components" / "nasa_astronomy" / "astronomy-cards.js",
    ROOT / "www" / "community" / "astronomy-cards" / "astronomy-cards.js",
)


def get_current_version() -> str:
    with open(VERSION_FILES["version_json"]) as f:
        return json.load(f)["version"]


def bump(version: str, part: str) -> str:
    major, minor, patch = [int(x) for x in version.split(".")]
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid part: {part}. Use major, minor, or patch.")


def plan_version_json(new_version: str) -> list[tuple[Path, str]]:
    path = VERSION_FILES["version_json"]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_version
    data["integration"] = new_version
    data["cards"] = new_version
    from datetime import date
    data["date"] = date.today().isoformat()
    return [(path, json.dumps(data, indent=2) + "\n")]


def plan_manifest(new_version: str) -> list[tuple[Path, str]]:
    path = VERSION_FILES["manifest"]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_version
    return [(path, json.dumps(data, indent=2) + "\n")]


def plan_package_json(new_version: str) -> list[tuple[Path, str]]:
    path = VERSION_FILES["package"]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = new_version
    return [(path, json.dumps(data, indent=2) + "\n")]


def plan_cards_js(new_version: str) -> list[tuple[Path, str]]:
    """Rewrite every version string in both copies of the card bundle.

    The patterns below are anchored on the strings that actually appear in the
    bundle. When the bundle was renamed from "NASA Astronomy Cards" the old
    patterns stopped matching and the banner silently drifted, so each
    substitution is verified and the script fails loudly instead.

    Note that ``Astronomy Space Suite Cards v`` is a *product name*, not a code
    identifier: the next rename will be done by someone who correctly believes
    they are not touching code, and this will stop matching again. That is the
    case this returns-rather-than-writes shape exists to make survivable.
    """
    patterns = (
        (r'(Astronomy Space Suite Cards v)\d+\.\d+\.\d+', "header/banner"),
        (r'(const VERSION = ")\d+\.\d+\.\d+', "VERSION constant"),
    )
    planned = []
    for path in CARDS_JS_FILES:
        content = path.read_text(encoding="utf-8")
        for pattern, label in patterns:
            content, count = re.subn(pattern, rf'\g<1>{new_version}', content)
            if not count:
                raise SystemExit(f"❌ {path.name}: no {label} version string matched {pattern!r}")
        planned.append((path, content))
    return planned


def git_tag_and_commit(new_version: str) -> None:
    tag = f"v{new_version}"
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"release: v{new_version}"],
        cwd=ROOT, check=True
    )
    subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
        cwd=ROOT, check=True
    )
    print(f"\n✅ Version bumped to {new_version}")
    print(f"   Tag: {tag}")
    print(f"\n   Push with: git push && git push --tags")


# Each step returns the writes it wants rather than performing them, so that a
# step which cannot do its job aborts the release before anything is touched.
# Adding a step here is abort-safe by construction; adding one that writes for
# itself reintroduces the half-bumped tree.
PLAN_STEPS = (
    ("version.json", plan_version_json),
    ("manifest.json", plan_manifest),
    ("package.json", plan_package_json),
    ("astronomy-cards.js (both copies)", plan_cards_js),
)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("major", "minor", "patch"):
        print("Usage: python scripts/bump_version.py [major|minor|patch] [--no-git]")
        sys.exit(1)

    part = sys.argv[1]
    no_git = "--no-git" in sys.argv
    current = get_current_version()
    new_version = bump(current, part)

    print(f"Bumping version: {current} → {new_version} ({part})")
    print()
    print("Validating:")

    # Phase 1: work out every replacement and verify each one matched. Any
    # SystemExit raised here leaves the working tree exactly as it was found.
    planned: list[tuple[Path, str]] = []
    for label, planner in PLAN_STEPS:
        planned.extend(planner(new_version))
        print(f"  ✓ {label}")

    # Phase 2: nothing above can fail on a pattern any more, so commit.
    for path, content in planned:
        path.write_text(content, encoding="utf-8")
    print(f"\n  {len(planned)} files written")

    if no_git:
        print(f"\n✅ Version bumped to {new_version} (git skipped)")
    else:
        git_tag_and_commit(new_version)


if __name__ == "__main__":
    main()
