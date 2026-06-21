#!/usr/bin/env python3
import argparse
import re
import sys
import json

MAKEFILE_PATH = "Makefile"
APP_JSON_PATH = "app.json"


def get_current_version() -> str | None:
    version = None
    # Read from Makefile first
    try:
        with open(MAKEFILE_PATH, "r") as f:
            content = f.read()
        match = re.search(r"^APP_VERSION\s*:=\s*([^\s#]+)", content, re.MULTILINE)
        if match:
            version = match.group(1).strip('"')
    except FileNotFoundError:
        pass

    if not version:
        # Fallback/cross-check with app.json
        try:
            with open(APP_JSON_PATH, "r") as f:
                data = json.load(f)
                version = data.get("version")
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    return version


def parse_semver(version_str: str) -> dict[str, int | str]:
    # Matches semantic versions e.g. 1.0.0, 1.0.0-beta.1, 1.0.0-dev.2+sha
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\.]+))?(?:\+([a-zA-Z0-9\.]+))?$"
    match = re.match(pattern, version_str)
    if not match:
        raise ValueError(f"Invalid semantic version: {version_str}")
    major, minor, patch, prerelease, build = match.groups()
    return {
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch),
        "prerelease": prerelease or "",
        "build": build or "",
    }


def stringify_semver(parsed: dict[str, int | str]) -> str:
    version = f"{parsed['major']}.{parsed['minor']}.{parsed['patch']}"
    if parsed["prerelease"]:
        version += f"-{parsed['prerelease']}"
    if parsed["build"]:
        version += f"+{parsed['build']}"
    return version


def bump_version(parsed: dict[str, int | str], bump_type: str) -> dict[str, int | str]:
    major = int(parsed["major"])
    minor = int(parsed["minor"])
    patch = int(parsed["patch"])
    prerelease = str(parsed["prerelease"])
    build = str(parsed["build"])

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
        prerelease = ""
        build = ""
    elif bump_type == "minor":
        minor += 1
        patch = 0
        prerelease = ""
        build = ""
    elif bump_type == "patch":
        patch += 1
        prerelease = ""
        build = ""
    elif bump_type == "beta":
        # e.g., 1.0.0-beta.0 -> 1.0.0-beta.1
        # or 1.0.0 -> 1.0.1-beta.0
        pre = prerelease
        if pre.startswith("beta."):
            try:
                num = int(pre.split(".")[1])
                prerelease = f"beta.{num + 1}"
            except ValueError:
                prerelease = "beta.0"
        else:
            if not pre:
                patch += 1
            prerelease = "beta.0"
        build = ""
    elif bump_type == "dev":
        pre = prerelease
        if pre.startswith("dev."):
            try:
                num = int(pre.split(".")[1])
                prerelease = f"dev.{num + 1}"
            except ValueError:
                prerelease = "dev.0"
        else:
            if not pre:
                patch += 1
            prerelease = "dev.0"
        build = ""

    parsed["major"] = major
    parsed["minor"] = minor
    parsed["patch"] = patch
    parsed["prerelease"] = prerelease
    parsed["build"] = build
    return parsed


def update_files(new_version: str, dry_run: bool = False) -> None:
    # Update Makefile
    try:
        with open(MAKEFILE_PATH, "r") as f:
            makefile_content = f.read()

        # Replace version line
        updated_makefile, count = re.subn(
            r"^(APP_VERSION\s*:=\s*)([^\s#]+)",
            f"\\g<1>{new_version}",
            makefile_content,
            flags=re.MULTILINE,
        )
        if count > 0:
            if dry_run:
                print(
                    f"[DRY-RUN] Would update {MAKEFILE_PATH} with APP_VERSION := {new_version}"
                )
            else:
                with open(MAKEFILE_PATH, "w") as f:
                    f.write(updated_makefile)
                print(f"Updated {MAKEFILE_PATH} version to {new_version}")
        else:
            print(f"Warning: APP_VERSION not found in {MAKEFILE_PATH}")
    except FileNotFoundError:
        print(f"Error: {MAKEFILE_PATH} not found.")

    # Update app.json
    try:
        with open(APP_JSON_PATH, "r") as f:
            app_json_data = json.load(f)

        old_val = app_json_data.get("version")
        app_json_data["version"] = new_version

        if dry_run:
            print(f"[DRY-RUN] Would update {APP_JSON_PATH} version to {new_version}")
        else:
            with open(APP_JSON_PATH, "w") as f:
                json.dump(app_json_data, f, indent=2)
            print(f"Updated {APP_JSON_PATH} version from {old_val} to {new_version}")
    except FileNotFoundError:
        print(f"Warning: {APP_JSON_PATH} not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to parse {APP_JSON_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage project semantic version.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--get", action="store_true", help="Print the current version.")
    group.add_argument("--set", help="Explicitly set a version.")
    group.add_argument(
        "--bump",
        choices=["major", "minor", "patch", "beta", "dev"],
        help="Bump version level.",
    )
    parser.add_argument("--build-metadata", help="Add build metadata (e.g. git SHA).")
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write changes to files."
    )

    args = parser.parse_args()

    current = get_current_version()
    if not current:
        print("Error: Could not retrieve current version.", file=sys.stderr)
        sys.exit(1)

    if args.get:
        print(current)
        sys.exit(0)

    try:
        parsed = parse_semver(current)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if args.set:
        new_version = args.set
    else:
        parsed = bump_version(parsed, args.bump)
        if args.build_metadata:
            parsed["build"] = args.build_metadata
        new_version = stringify_semver(parsed)

    update_files(new_version, args.dry_run)


if __name__ == "__main__":
    main()
