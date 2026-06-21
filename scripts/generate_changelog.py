#!/usr/bin/env python3
import argparse
import subprocess
import re
import sys

# Category mapping based on conventional commits
CATEGORIES = {
    "feat": "🚀 Features",
    "fix": "🐛 Bug Fixes",
    "docs": "📝 Documentation",
    "style": "🎨 Styling",
    "refactor": "♻️ Refactoring",
    "perf": "⚡ Performance",
    "test": "🧪 Tests",
    "chore": "🧹 Maintenance",
    "ci": "🤖 CI/CD & Automation",
    "breaking": "⚠️ Breaking Changes"
}

def get_git_commits(start_ref=None, end_ref="HEAD"):
    cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%s"]
    if start_ref:
        cmd.append(f"{start_ref}..{end_ref}")
    else:
        cmd.append(end_ref)
        
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError:
        # Fallback if range fails or repo has no commits
        return []
        
    commits = []
    for line in output.strip().split("\n"):
        if not line or "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author_name": parts[1],
                "author_email": parts[2],
                "subject": parts[3]
            })
    return commits

def clean_subject(subject):
    # Strip conventional commit scope/type if present, e.g. "feat(sw): add user profile" -> "add user profile"
    match = re.match(r"^[a-z]+(?:\([a-zA-Z0-9_\-\/]+\))?!?:\s*(.*)", subject, re.IGNORECASE)
    if match:
        subject = match.group(1)
    
    # Strip common ending punctuation/prepositions/whitespace
    subject = subject.strip().rstrip(".!?,")
    # Normalize multiple whitespaces
    subject = re.sub(r"\s+", " ", subject)
    return subject

def parse_commit_type(subject):
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

def is_noise(subject, author_name):
    # Noise filters from sibling projects
    if "dependabot" in author_name.lower() or "github-actions" in author_name.lower():
        return True
    sub_lower = subject.lower()
    if len(sub_lower) < 5:
        return True
    if any(x in sub_lower for x in ["wip", "initial commit", "update", "bump version", "release v"]):
        # Match only trivial/empty generic logs
        if sub_lower in ["wip", "initial commit", "update", "temp", "test"]:
            return True
    return False

def generate_changelog(start_ref, end_ref="HEAD", limit=15):
    commits = get_git_commits(start_ref, end_ref)
    
    categorized = {k: [] for k in CATEGORIES.values()}
    breaking_notes = []
    contributors = set()
    seen_normalized = set()
    
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
        # (Assuming fabian-seitz is the primary maintainer)
        attribution = ""
        if "fabian-seitz" not in author.lower() and "fabian" not in author.lower():
            attribution = f" (thanks to @{author})"
            contributors.add(author)
            
        short_hash = c["hash"][:7]
        entry = f"- {clean_subject(subj)} ({short_hash}){attribution}"
        
        if c_type == "breaking":
            breaking_notes.append(entry)
        
        categorized[cat_name].append(entry)
        
    # Output MD building
    md_output = []
    
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
        md_output.append("A special thank you to all contributors who helped with this release:")
        for user in sorted(contributors):
            md_output.append(f"- @{user}")
        md_output.append("")
        
    if not md_output:
        md_output.append("No user-facing changes since last release.")
        
    return "\n".join(md_output)

def main():
    # Force stdout to be utf-8 for Windows shells
    sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description="Generate markdown changelog from git history.")
    parser.add_argument("--start", help="Starting commit tag/hash (default: latest tag).")
    parser.add_argument("--end", default="HEAD", help="Ending commit tag/hash (default: HEAD).")
    parser.add_argument("--limit", type=int, default=15, help="Number of entries before folding.")
    parser.add_argument("--dry-run", action="store_true", help="Print changelog instead of saving.")
    
    args = parser.parse_args()
    
    start_ref = args.start
    if not start_ref:
        # Find latest tag
        try:
            start_ref = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            # Fallback to entire history if no tags exist
            start_ref = None
            
    changelog = generate_changelog(start_ref, args.end, args.limit)
    print(changelog)

if __name__ == "__main__":
    main()
