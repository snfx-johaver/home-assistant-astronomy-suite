#!/usr/bin/env python3
"""
Version bump script for Home Assistant Astronomy Suite.

Usage:
  python scripts/bump_version.py [major|minor|patch]

Updates version in all files:
  - version.json
  - custom_components/nasa_astronomy/manifest.json
  - www/community/astronomy-cards/package.json
  - www/community/astronomy-cards/astronomy-cards.js (console banner)

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
    "cards_js": ROOT / "www" / "community" / "astronomy-cards" / "astronomy-cards.js",
}


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


def update_version_json(new_version: str) -> None:
    path = VERSION_FILES["version_json"]
    with open(path) as f:
        data = json.load(f)
    data["version"] = new_version
    data["integration"] = new_version
    data["cards"] = new_version
    from datetime import date
    data["date"] = date.today().isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def update_manifest(new_version: str) -> None:
    path = VERSION_FILES["manifest"]
    with open(path) as f:
        data = json.load(f)
    data["version"] = new_version
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def update_package_json(new_version: str) -> None:
    path = VERSION_FILES["package"]
    with open(path) as f:
        data = json.load(f)
    data["version"] = new_version
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def update_cards_js(new_version: str) -> None:
    path = VERSION_FILES["cards_js"]
    content = path.read_text(encoding="utf-8")
    # Update the console.info version banner
    content = re.sub(
        r'(%c NASA-ASTRONOMY-CARDS %c v)\d+\.\d+\.\d+',
        rf'\g<1>{new_version}',
        content
    )
    # Update the top comment
    content = re.sub(
        r'(NASA Astronomy Cards v)\d+\.\d+\.\d+',
        rf'\g<1>{new_version}',
        content
    )
    path.write_text(content, encoding="utf-8")


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

    update_version_json(new_version)
    print(f"  ✓ version.json")

    update_manifest(new_version)
    print(f"  ✓ manifest.json")

    update_package_json(new_version)
    print(f"  ✓ package.json")

    update_cards_js(new_version)
    print(f"  ✓ astronomy-cards.js")

    if no_git:
        print(f"\n✅ Version bumped to {new_version} (git skipped)")
    else:
        git_tag_and_commit(new_version)


if __name__ == "__main__":
    main()
