#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys

MAKEFILE_PATH = "Makefile"
APP_JSON_PATH = "app.json"


def get_current_version() -> str:
    """Get current version from git tags first, then app.json, then Makefile."""
    try:
        tags = (
            subprocess.check_output(["git", "tag"], stderr=subprocess.DEVNULL)
            .decode()
            .splitlines()
        )
        v_tags = []
        for tag in tags:
            tag = tag.strip()
            match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:(b)(\d+)|(\.dev)(\d+))?$", tag)
            if match:
                y, m, p, bp, bn, dp, dn = match.groups()
                v_tags.append(
                    {
                        "tag": tag,
                        "key": (
                            int(y),
                            int(m),
                            int(p),
                            (1 if bp else (0 if dp else 2)),
                            (int(bn) if bp else (int(dn) if dp else 0)),
                        ),
                    }
                )
        if v_tags:
            return sorted(v_tags, key=lambda x: x["key"], reverse=True)[0][
                "tag"
            ].lstrip("v")
    except subprocess.CalledProcessError:
        pass

    # Fallback: app.json
    try:
        with open(APP_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Fallback: Makefile
    try:
        with open(MAKEFILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"^APP_VERSION\s*:=\s*([^\s#]+)", content, re.MULTILINE)
        if match:
            return match.group(1).strip('"')
    except FileNotFoundError:
        pass

    return "0.0.0"


def calculate_version(
    rtype: str,
    level: str = "patch",
    curr: str | None = None,
    override: str | None = None,
) -> str:
    if override and override.strip():
        return override.strip().lstrip("v")

    if curr is None:
        curr = get_current_version()

    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)(?:(b)(\d+)|(\.dev)(\d+))?$", curr)
    if not match:
        return "0.0.0"

    v1_str, v2_str, v3_str, b_p, b_n, d_p, d_n = match.groups()
    v1, v2, v3 = int(v1_str), int(v2_str), int(v3_str)
    stype = "b" if b_p else (".dev" if d_p else None)
    snum = int(b_n) if b_p else (int(d_n) if d_p else 0)

    if rtype == "stable":
        if stype:
            return f"{v1}.{v2}.{v3}"
        if level == "major":
            return f"{v1 + 1}.0.0"
        if level == "minor":
            return f"{v1}.{v2 + 1}.0"
        return f"{v1}.{v2}.{v3 + 1}"
    if rtype == "beta":
        if stype == "b":
            return f"{v1}.{v2}.{v3}b{snum + 1}"
        if level == "major":
            return f"{v1 + 1}.0.0b0"
        if level == "minor":
            return f"{v1}.{v2 + 1}.0b0"
        return f"{v1}.{v2}.{v3 + 1}b0"
    if rtype in ["dev", "nightly"]:
        if stype == ".dev":
            return f"{v1}.{v2}.{v3}.dev{snum + 1}"
        if level == "major":
            return f"{v1 + 1}.0.0.dev0"
        if level == "minor":
            return f"{v1}.{v2 + 1}.0.dev0"
        return f"{v1}.{v2}.{v3 + 1}.dev0"

    return curr


def write_version(new_version: str) -> None:
    # Update Makefile
    try:
        with open(MAKEFILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        updated, count = re.subn(
            r"^(APP_VERSION\s*:=\s*)([^\s#]+)",
            rf"\g<1>{new_version}",
            content,
            flags=re.MULTILINE,
        )
        if count > 0:
            with open(MAKEFILE_PATH, "w", encoding="utf-8") as f:
                f.write(updated)
            print(
                f"Updated {MAKEFILE_PATH} APP_VERSION → {new_version}", file=sys.stderr
            )
    except FileNotFoundError:
        pass

    # Update app.json
    try:
        with open(APP_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["version"] = new_version
        with open(APP_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"Updated {APP_JSON_PATH} version → {new_version}", file=sys.stderr)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage project semantic version.")
    subparsers = parser.add_subparsers(dest="command")

    # ha-openwrt-style subcommand: scripts/version_manager.py bump --type stable --level patch
    bump_parser = subparsers.add_parser("bump")
    bump_parser.add_argument(
        "--type", choices=["stable", "beta", "dev", "nightly"], required=True
    )
    bump_parser.add_argument(
        "--level", choices=["major", "minor", "patch"], default="patch"
    )
    bump_parser.add_argument("--override", default=None)

    # Legacy flat flags kept for backward compat
    parser.add_argument("--get", action="store_true", help="Print current version.")
    parser.add_argument("--set", help="Set explicit version.")
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch", "beta", "dev"],
        help="Bump version (legacy flat mode).",
    )

    args = parser.parse_args()

    current = get_current_version()

    if args.command == "bump":
        override_val = (
            args.override if args.override and args.override.strip() else None
        )
        new_v = calculate_version(args.type, args.level, override=override_val)
        write_version(new_v)
        print(new_v)
        return

    # Legacy flat mode
    if args.get:
        print(current)
        return

    if args.set:
        write_version(args.set)
        return

    if args.bump:
        type_map = {
            "major": ("stable", "major"),
            "minor": ("stable", "minor"),
            "patch": ("stable", "patch"),
            "beta": ("beta", "patch"),
            "dev": ("dev", "patch"),
        }
        rtype, level = type_map[args.bump]
        new_v = calculate_version(rtype, level, curr=current)
        write_version(new_v)
        print(new_v)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
