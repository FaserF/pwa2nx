#!/usr/bin/env python3
import argparse
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PWA metadata and assets")
    parser.add_argument("--url", required=True, help="Website URL")
    parser.add_argument("--name", required=True, help="Fallback App Name")
    parser.add_argument("--icon", default="", help="Fallback Icon URL")
    parser.add_argument(
        "--output-icon", default="source/icon.png", help="Output path for Switch icon"
    )
    parser.add_argument(
        "--output-hdr",
        default="source/config.h",
        help="Output path for C config header",
    )
    return parser.parse_args()


def fetch_manifest_url(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 PWA2NX"})
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.find("link", rel=lambda x: x and "manifest" in x.lower())
        if link:
            href = link.get("href")
            if href and isinstance(href, str):
                return urljoin(url, href)
    except Exception as e:
        print(f"Error fetching page for manifest: {e}")
    return None


def download_and_resize_icon(icon_url: str, dest_path: str) -> bool:
    try:
        r = requests.get(icon_url, timeout=10, stream=True)
        if r.status_code == 200:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path + ".tmp", "wb") as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)

            # Resize to 256x256 PNG
            with Image.open(dest_path + ".tmp") as img:
                resized_img = img.resize((256, 256), Image.Resampling.LANCZOS)
                resized_img.save(dest_path, "PNG")
            os.remove(dest_path + ".tmp")
            print(f"Successfully processed icon: {dest_path}")
            return True
    except Exception as e:
        print(f"Failed to process icon from {icon_url}: {e}")
    return False


def generate_default_icon(dest_path: str) -> None:
    # Generates a standard grid fallback icon
    img = Image.new("RGBA", (256, 256), color=(44, 62, 80, 255))
    img.save(dest_path, "PNG")
    print(f"Generated placeholder icon at {dest_path}")


def main() -> None:
    args = parse_args()
    app_name = args.name
    target_url = args.url
    icon_src = args.icon

    is_universal = target_url.strip().lower() == "universal"

    manifest_url = None if is_universal else fetch_manifest_url(target_url)
    manifest_data = {}

    if manifest_url:
        try:
            mr = requests.get(manifest_url, timeout=10)
            if mr.status_code == 200:
                manifest_data = mr.json()
                app_name = manifest_data.get(
                    "short_name", manifest_data.get("name", app_name)
                )
                print(f"PWA Found! App Name: {app_name}")
        except Exception as e:
            print(f"Could not parse manifest at {manifest_url}: {e}")

    # Deduce icon url
    found_icon = False
    if "icons" in manifest_data and manifest_data["icons"]:
        # Sort icons to find the largest or one matching 256/512
        icons = manifest_data["icons"]
        best_icon = sorted(
            icons,
            key=lambda x: (
                int(x.get("sizes", "0").split("x")[0])
                if "x" in x.get("sizes", "")
                else 0
            ),
            reverse=True,
        )[0]
        icon_href = best_icon.get("src")
        if icon_href:
            best_icon_url = urljoin(manifest_url or target_url, icon_href)
            print(f"PWA Icon identified: {best_icon_url}")
            found_icon = download_and_resize_icon(best_icon_url, args.output_icon)

    if not found_icon and icon_src:
        print(f"Attempting fallback icon URL: {icon_src}")
        found_icon = download_and_resize_icon(icon_src, args.output_icon)

    if not found_icon:
        if os.path.exists(args.output_icon):
            print(
                f"No custom PWA icon fetched. Preserving existing fallback icon at {args.output_icon}"
            )
        else:
            generate_default_icon(args.output_icon)

    # Extract GITHUB_REPO from env, app.json, or fallback
    import json

    repo_owner_name = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo_owner_name:
        try:
            if os.path.exists("app.json"):
                with open("app.json", "r") as r_file:
                    app_data = json.load(r_file)
                    repo_url = app_data.get("repository", "")
                    rmatch = re.search(r"github\.com/([^/]+/[^/]+)", repo_url)
                    if rmatch:
                        repo_owner_name = rmatch.group(1).rstrip(".git")
        except Exception as e:
            print(f"Error parsing app.json for repo: {e}")

    if not repo_owner_name:
        repo_owner_name = "FaserF/pwa2nx"

    safe_app_name = re.sub(r"[^a-zA-Z0-9]", "_", app_name)

    # Determine background playback setting (enabled for Spotify, SoundCloud, YT Music, Universal App)
    bg_playback = "0"
    bg_apps = ["spotify", "soundcloud", "yt music", "youtube music", "universal app"]
    if app_name.lower() in bg_apps or target_url.lower() == "universal":
        bg_playback = "1"

    # Write C header config
    os.makedirs(os.path.dirname(args.output_hdr), exist_ok=True)
    with open(args.output_hdr, "w") as f:
        f.write("/* Auto-generated by pwa2nx */\n")
        f.write("#pragma once\n\n")
        f.write(f'#define APP_TITLE "{app_name}"\n')
        f.write(f'#define TARGET_URL "{target_url}"\n')
        f.write(f'#define SAFE_NAME "{safe_app_name}"\n')
        f.write(f'#define GITHUB_REPO "{repo_owner_name}"\n')
        f.write(f"#define ENABLE_BACKGROUND_PLAYBACK {bg_playback}\n")

    print("Metadata generation complete.")


if __name__ == "__main__":
    main()
