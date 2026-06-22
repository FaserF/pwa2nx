import os
import json


def main() -> None:
    # 1. Gather Metadata
    metadata = {
        "name": "pwa2nx",
        "description": "Convert Progressive Web Apps (PWAs) and standard websites into native wrappers on the Nintendo Switch utilizing the internal NetFront NX WebKit applet.",
        "entry_points": {
            "c_main": "source/main.c",
            "python_script": "scripts/extract_pwa.py",
        },
    }

    # 2. Populate File Tree
    file_tree = {
        "source": "C source files and configurations for the Nintendo Switch wrapper",
        "source/main.c": "Primary entry point of the Switch applet wrapper handling keyboard, profile, and WebKit launch",
        "source/updater.c": "GitHub Release OTA self-updater using libcurl",
        "source/updater.h": "Header for updater module",
        "source/config.h": "Auto-generated target URL and title configuration header",
        "source/icon.jpg": "The 256x256 icon of the application packaged into the NRO",
        "scripts": "Helper python scripts for build-time operations",
        "scripts/extract_pwa.py": "Downloads PWA manifests, extracts/resizes icons, and writes C configuration headers",
        "Makefile": "devkitPro compiler makefile configuring flags, libnx libraries, and compilation tasks",
        "app.json": "Metadata structure for Homebrew App Store distribution compatibility",
        ".github/workflows/build-and-release.yml": "CI/CD pipeline triggering automated PWA extraction, NRO compilation, and GitHub Release generation",
    }

    manifest = {"metadata": metadata, "file_tree": file_tree}

    # Write Manifest if it changed
    manifest_path = "project_manifest.json"
    new_content = json.dumps(manifest, indent=2) + "\n"

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            old_content = f.read()
        if old_content == new_content:
            print("project_manifest.json is up to date.")
            return

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Generated project_manifest.json")


if __name__ == "__main__":
    main()
