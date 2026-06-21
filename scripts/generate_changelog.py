#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys
import os
import json

# Category mapping based on conventional commits
CATEGORIES: dict[str, str] = {
    "feat": "🚀 Features",
    "fix": "🐛 Bug Fixes",
    "docs": "📝 Documentation",
    "style": "🎨 Styling",
    "refactor": "♻️ Refactoring",
    "perf": "⚡ Performance",
    "test": "🧪 Tests",
    "chore": "🧹 Maintenance",
    "ci": "🤖 CI/CD & Automation",
    "breaking": "⚠️ Breaking Changes",
}


def get_git_commits(
    start_ref: str | None = None, end_ref: str = "HEAD"
) -> list[dict[str, str]]:
    cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%s"]
    if start_ref:
        cmd.append(f"{start_ref}..{end_ref}")
    else:
        cmd.append(end_ref)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode(
            "utf-8", errors="ignore"
        )
    except subprocess.CalledProcessError:
        # Fallback if range fails or repo has no commits
        return []

    commits: list[dict[str, str]] = []
    for line in output.strip().split("\n"):
        if not line or "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append(
                {
                    "hash": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "subject": parts[3],
                }
            )
    return commits


def clean_subject(subject: str) -> str:
    # Strip conventional commit scope/type if present, e.g. "feat(sw): add user profile" -> "add user profile"
    match = re.match(
        r"^[a-z]+(?:\([a-zA-Z0-9_\-\/]+\))?!?:\s*(.*)", subject, re.IGNORECASE
    )
    if match:
        subject = match.group(1)

    # Strip common ending punctuation/prepositions/whitespace
    subject = subject.strip().rstrip(".!?,")
    # Normalize multiple whitespaces
    subject = re.sub(r"\s+", " ", subject)
    return subject


def parse_commit_type(subject: str) -> str:
    # Check for breaking change indicator
    if "breaking change" in subject.lower() or "!" in subject.split(":")[0]:
        return "breaking"

    match = re.match(r"^([a-z]+)(?:\([^\)]+\))?:", subject, re.IGNORECASE)
    if match:
        c_type = match.group(1).lower()
        if c_type in CATEGORIES:
            return c_type

    # Heuristic categorization if conventional prefix is missing
    sub_lower = subject.lower()
    if any(x in sub_lower for x in ["fix", "bug", "patch"]):
        return "fix"
    if any(x in sub_lower for x in ["feat", "add", "new", "implement"]):
        return "feat"
    if any(x in sub_lower for x in ["doc", "readme", "wiki"]):
        return "docs"
    if any(x in sub_lower for x in ["test", "unittest", "pytest"]):
        return "test"
    if any(x in sub_lower for x in ["clean", "refactor", "simplify"]):
        return "refactor"

    return "chore"


def is_noise(subject: str, author_name: str) -> bool:
    # Noise filters from sibling projects
    if "dependabot" in author_name.lower() or "github-actions" in author_name.lower():
        return True
    sub_lower = subject.lower()
    if len(sub_lower) < 5:
        return True
    if any(
        x in sub_lower
        for x in ["wip", "initial commit", "update", "bump version", "release v"]
    ):
        # Match only trivial/empty generic logs
        if sub_lower in ["wip", "initial commit", "update", "temp", "test"]:
            return True
    return False


def get_primary_maintainers() -> set[str]:
    maintainers = {"faserf", "faser", "fabian-seitz"}  # safety fallbacks
    # Try reading from app.json
    try:
        if os.path.exists("app.json"):
            with open("app.json", "r") as f:
                data = json.load(f)
                author = data.get("author")
                if author:
                    maintainers.add(author.lower())
                    # extract first word in case of full name
                    maintainers.add(author.split()[0].lower())
    except Exception:
        pass

    # Try reading from git remote
    try:
        url = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        # matches https://github.com/owner/repo.git or git@github.com:owner/repo.git
        match = re.search(r"github\.com[:/]([^/]+)/", url)
        if match:
            owner = match.group(1).lower()
            maintainers.add(owner)
            if "-" in owner:
                maintainers.add(owner.split("-")[0])
    except Exception:
        pass

    return maintainers


def generate_changelog(
    start_ref: str | None, end_ref: str = "HEAD", limit: int = 15
) -> str:
    commits = get_git_commits(start_ref, end_ref)
    maintainers = get_primary_maintainers()

    categorized: dict[str, list[str]] = {k: [] for k in CATEGORIES.values()}
    breaking_notes: list[str] = []
    contributors: set[str] = set()
    seen_normalized: set[str] = set()

    for c in commits:
        subj = c["subject"]
        author = c["author_name"]

        # Noise filter
        if is_noise(subj, author):
            continue

        # Deduplication / Normalization check
        norm = clean_subject(subj).lower()
        if norm in seen_normalized:
            continue
        seen_normalized.add(norm)

        # Determine category
        c_type = parse_commit_type(subj)
        cat_name = CATEGORIES[c_type]

        # Author attribution logic for external/non-standard contributors
        attribution = ""
        is_maintainer = False
        author_lower = author.lower()
        for m in maintainers:
            if m in author_lower:
                is_maintainer = True
                break

        if not is_maintainer:
            attribution = f" (thanks to @{author})"
            contributors.add(author)

        short_hash = c["hash"][:7]
        entry = f"- {clean_subject(subj)} ({short_hash}){attribution}"

        if c_type == "breaking":
            breaking_notes.append(entry)

        categorized[cat_name].append(entry)

    # Output MD building
    md_output: list[str] = []

    # 1. Breaking section (Banner layout)
    if breaking_notes:
        md_output.append("> [!CAUTION]\n> **BREAKING CHANGES**")
        for note in breaking_notes:
            md_output.append(f"> {note}")
        md_output.append("")

    # 2. Main sections
    for cat_name, entries in categorized.items():
        if not entries:
            continue
        # Skip breaking from duplicates if we already put it in the alert banner
        if cat_name == CATEGORIES["breaking"]:
            continue

        md_output.append(f"### {cat_name}")

        # Collapsible fold if there are too many items
        if len(entries) > limit:
            md_output.append("<details>")
            md_output.append(f"<summary>View all {len(entries)} changes</summary>\n")
            md_output.extend(entries)
            md_output.append("\n</details>\n")
        else:
            md_output.extend(entries)
            md_output.append("")

    # 3. Contributor attribution section
    if contributors:
        md_output.append("### 💖 Contributors")
        md_output.append(
            "A special thank you to all contributors who helped with this release:"
        )
        for user in sorted(contributors):
            md_output.append(f"- @{user}")
        md_output.append("")

    if not md_output:
        md_output.append("No user-facing changes since last release.")

    return "\n".join(md_output)


def main() -> None:
    # Force stdout to be utf-8 for Windows shells
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    parser = argparse.ArgumentParser(
        description="Generate markdown changelog from git history."
    )
    parser.add_argument(
        "--start", help="Starting commit tag/hash (default: latest tag)."
    )
    parser.add_argument(
        "--end", default="HEAD", help="Ending commit tag/hash (default: HEAD)."
    )
    parser.add_argument(
        "--limit", type=int, default=15, help="Number of entries before folding."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print changelog instead of saving."
    )

    args = parser.parse_args()

    start_ref = args.start
    if not start_ref:
        # Find latest tag
        try:
            start_ref = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )
        except subprocess.CalledProcessError:
            # Fallback to entire history if no tags exist
            start_ref = None

    changelog = generate_changelog(start_ref, args.end, args.limit)
    print(changelog)


if __name__ == "__main__":
    main()
