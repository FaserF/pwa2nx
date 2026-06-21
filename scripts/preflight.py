#!/usr/bin/env python3
import os
import sys
import json
import subprocess
from PIL import Image

def check_makefile():
    print("Checking Makefile...")
    if not os.path.exists("Makefile"):
        print("[-] Error: Makefile does not exist.")
        return False
    
    with open("Makefile", "r") as f:
        content = f.read()
        
    required_vars = ["APP_TITLE", "APP_VERSION", "APP_AUTHOR"]
    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)
            
    if missing:
        print(f"[-] Error: Makefile is missing required variables: {', '.join(missing)}")
        return False
        
    print("[+] Makefile check passed.")
    return True

def check_app_json():
    print("Checking app.json...")
    if not os.path.exists("app.json"):
        print("[-] Error: app.json does not exist.")
        return False
        
    try:
        with open("app.json", "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[-] Error: app.json is not valid JSON: {e}")
        return False
        
    required_keys = ["name", "author", "version", "category", "description"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"[-] Error: app.json is missing required properties: {', '.join(missing)}")
        return False
        
    print("[+] app.json check passed.")
    return True

def check_icon():
    print("Checking source/icon.png...")
    icon_path = os.path.join("source", "icon.png")
    if not os.path.exists(icon_path):
        print(f"[-] Error: Icon file does not exist at {icon_path}")
        return False
        
    try:
        with Image.open(icon_path) as img:
            width, height = img.size
            if width != 256 or height != 256:
                print(f"[-] Error: Icon size must be 256x256, but found {width}x{height}.")
                return False
            if img.format != "PNG":
                print(f"[-] Error: Icon must be in PNG format, but found {img.format}.")
                return False
    except Exception as e:
        print(f"[-] Error reading icon: {e}")
        return False
        
    print("[+] Icon check passed.")
    return True

def check_tag_collision():
    print("Checking git tag collisions...")
    # Get current version from app.json
    try:
        with open("app.json", "r") as f:
            version = json.load(f).get("version")
    except Exception:
        print("[-] Skip tag collision check: unable to read version from app.json.")
        return True
        
    tag_name = f"v{version}"
    try:
        tags = subprocess.check_output(["git", "tag"]).decode("utf-8").split()
        if tag_name in tags:
            # Check if we are running in a CI re-release mode
            if os.getenv("ALLOW_RE_RELEASE") == "true":
                print(f"[!] Warning: Git tag {tag_name} already exists but ALLOW_RE_RELEASE is true. Proceeding.")
                return True
            print(f"[-] Error: Git tag {tag_name} already exists. Increment version or enable re-release.")
            return False
    except subprocess.CalledProcessError:
        # Git tag may fail if not in a git repo or no tags exist
        pass
        
    print("[+] Tag collision check passed.")
    return True

def main():
    success = True
    success &= check_makefile()
    success &= check_app_json()
    success &= check_icon()
    success &= check_tag_collision()
    
    if not success:
        print("\n[-] Preflight checks failed!")
        sys.exit(1)
        
    print("\n[+] All preflight checks passed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
