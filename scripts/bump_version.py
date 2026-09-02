#!/usr/bin/env python3
"""
Version bump script for Home Assistant Astronomy Suite.

Usage:
  python scripts/bump_version.py [major|minor|patch]

Updates version in all files:
  - version.json
  - custom_components/nasa_astronomy/manifest.json
  - custom_components/nasa_astronomy/__init__.py
  - www/community/astronomy-cards/package.json
  - astronomy-cards.js in BOTH locations (header comment, VERSION, console banner)

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
    "init_py": ROOT / "custom_components" / "nasa_astronomy" / "__init__.py",
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
    """Rewrite every version string in both copies of the card bundle.

    The patterns below are anchored on the strings that actually appear in the
    bundle. When the bundle was renamed from "NASA Astronomy Cards" the old
    patterns stopped matching and the banner silently drifted, so each
    substitution is now verified and the script fails loudly instead.
    """
    patterns = (
        (r'(Astronomy Space Suite Cards v)\d+\.\d+\.\d+', "header/banner"),
        (r'(const VERSION = ")\d+\.\d+\.\d+', "VERSION constant"),
    )
    for path in CARDS_JS_FILES:
        content = path.read_text(encoding="utf-8")
        for pattern, label in patterns:
            content, count = re.subn(pattern, rf'\g<1>{new_version}', content)
            if not count:
                raise SystemExit(f"❌ {path.name}: no {label} version string matched {pattern!r}")
        path.write_text(content, encoding="utf-8")


def update_init_py(new_version: str) -> None:
    path = VERSION_FILES["init_py"]
    content = path.read_text(encoding="utf-8")
    content, count = re.subn(r'(^VERSION = ")\d+\.\d+\.\d+', rf'\g<1>{new_version}', content, flags=re.M)
    if not count:
        raise SystemExit("❌ __init__.py: no VERSION constant matched")
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

    update_init_py(new_version)
    print(f"  ✓ __init__.py")

    update_cards_js(new_version)
    print(f"  ✓ astronomy-cards.js (both copies)")

    if no_git:
        print(f"\n✅ Version bumped to {new_version} (git skipped)")
    else:
        git_tag_and_commit(new_version)


if __name__ == "__main__":
    main()
