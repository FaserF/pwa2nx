# -*- coding: utf-8 -*-
import os
import re
import sys
import urllib.request
import json

def get_latest_atmosphere_version():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request("https://api.github.com/repos/Atmosphere-NX/Atmosphere/releases/latest", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data['tag_name'].lstrip('v')
    except Exception as e:
        print(f"Error fetching Atmosphere version: {e}")
        return "1.6.2"

def update_template(file_path, app_version, atmosphere_version):
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Update app_version placeholder
    # Search for id: app_version ... placeholder: e.g. X.Y.Z
    # We update the line placeholder: ... under id: app_version
    pattern_app = r'(id:\s*app_version\s+attributes:\s+label:[^\n]+\n\s+description:[^\n]+\n\s+placeholder:\s*)([^\n]+)'
    content = re.sub(pattern_app, r'\1e.g. ' + app_version, content)

    # 2. Update cfw_version placeholder
    pattern_cfw = r'(id:\s*cfw_version\s+attributes:\s+label:[^\n]+\n\s+description:[^\n]+\n\s+placeholder:\s*)([^\n]+)'
    content = re.sub(pattern_cfw, r'\1e.g. Atmosphere ' + atmosphere_version, content)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python update_templates.py <version>")
        sys.exit(1)
        
    version = sys.argv[1].lstrip('v')
    atmosphere_ver = get_latest_atmosphere_version()
    
    bug_report_path = ".github/ISSUE_TEMPLATE/bug_report.yml"
    if update_template(bug_report_path, version, atmosphere_ver):
        print(f"Successfully updated placeholders in {bug_report_path} with App v{version} and Atmosphere v{atmosphere_ver}")
    else:
        print(f"Failed to find or update {bug_report_path}")

if __name__ == "__main__":
    main()
