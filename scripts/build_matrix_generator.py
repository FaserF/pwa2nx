#!/usr/bin/env python3
import json
import os
import sys

SUPPORTED_APPS_FILE = "supported_apps.json"


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/build_matrix_generator.py <app_selection> [new_app_name] [new_app_url] [new_app_icon]"
        )
        sys.exit(1)

    app_selection = sys.argv[1].strip()

    # Load current apps
    if os.path.exists(SUPPORTED_APPS_FILE):
        with open(SUPPORTED_APPS_FILE, "r", encoding="utf-8") as f:
            apps = json.load(f)
    else:
        apps = []

    selected_apps = []

    if app_selection == "new":
        if len(sys.argv) < 4:
            print("Error: For 'new' app selection, name and URL are required.")
            sys.exit(1)
        new_name = sys.argv[2].strip()
        new_url = sys.argv[3].strip()
        new_icon = sys.argv[4].strip() if len(sys.argv) > 4 else ""

        # Check if already exists, else append
        exists = False
        for a in apps:
            if a["name"].lower() == new_name.lower():
                a["url"] = new_url
                a["icon"] = new_icon
                exists = True
                selected_apps.append(a)
                break

        if not exists:
            new_app = {"name": new_name, "url": new_url, "icon": new_icon}
            apps.append(new_app)
            selected_apps.append(new_app)

            # Save the new app to repo immediately so build container handles it
            with open(SUPPORTED_APPS_FILE, "w", encoding="utf-8") as f:
                json.dump(apps, f, indent=2)
                f.write("\n")
            print(f"Added and saved new PWA target: {new_name}")

    elif app_selection.lower() == "all":
        selected_apps = apps
    else:
        # Split by comma for multiple selection
        selections = [s.strip().lower() for s in app_selection.split(",")]
        for s in selections:
            found = False
            for a in apps:
                # Match exact name, or if app name contains the search term
                a_lower = a["name"].lower()
                if a_lower == s or a_lower.startswith(s) or s in a_lower:
                    selected_apps.append(a)
                    found = True
                    break
            if not found:
                print(f"Warning: Selected app '{s}' not found in supported_apps.json")

    # Output JSON matrix format for GitHub Actions
    matrix_output = {"include": selected_apps}
    print(json.dumps(matrix_output))


if __name__ == "__main__":
    main()
