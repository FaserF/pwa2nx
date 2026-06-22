import os
import sys
import glob

def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "FaserF/pwa2nx")
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    
    nro_files = sorted(glob.glob("artifacts/*.nro"))
    nsp_files = sorted(glob.glob("artifacts/*.nsp"))
    
    has_nsp = len(nsp_files) > 0
    
    # Print mini-instructions at the top
    print("### ℹ️ Installation Instructions\n")
    print("* **NRO File (Homebrew Launcher):**")
    print("  - Place the `.nro` file in the `/switch/pwa2nx/` directory on your SD card.")
    print("  - Launch it using the Homebrew Launcher (preferably via Title Takeover / holding `R` while launching a game to avoid memory limits).\n")
    print("* **NSP File (Home Screen Channel):**")
    print("  - Install the `.nsp` file using any Switch title installer (such as Goldleaf, Awoo, or Tinfoil).")
    print("  - **Important:** The NSP is a forwarder. It requires the corresponding `.nro` file to be present in `/switch/pwa2nx/[PWA_NAME].nro` on your SD card to function.\n")
    
    if nro_files:
        print("### 🎮 Available PWAs in this Release\n")
        if has_nsp:
            print("| PWA | NRO (Homebrew) | NSP (Home Screen) | Downloads |")
            print("| :--- | :--- | :--- | :--- |")
            for nro_path in nro_files:
                nro_name = os.path.basename(nro_path)
                pwa_name = os.path.splitext(nro_name)[0].replace("_", " ")
                
                nro_url = f"https://github.com/{repo}/releases/download/{tag}/{nro_name}"
                nro_badge = f"https://img.shields.io/github/downloads/{repo}/{tag}/{nro_name}?label=NRO&style=flat-square&color=blue"
                
                # Check if matching NSP exists
                nsp_name = nro_name.replace(".nro", ".nsp")
                nsp_path = os.path.join("artifacts", nsp_name)
                
                if os.path.exists(nsp_path):
                    nsp_url = f"https://github.com/{repo}/releases/download/{tag}/{nsp_name}"
                    nsp_badge = f"https://img.shields.io/github/downloads/{repo}/{tag}/{nsp_name}?label=NSP&style=flat-square&color=green"
                    nsp_cell = f"[{nsp_name}]({nsp_url})"
                    badge_cell = f"![{pwa_name} NRO Downloads]({nro_badge}) ![{pwa_name} NSP Downloads]({nsp_badge})"
                else:
                    nsp_cell = "-"
                    badge_cell = f"![{pwa_name} NRO Downloads]({nro_badge})"
                    
                print(f"| **{pwa_name}** | [{nro_name}]({nro_url}) | {nsp_cell} | {badge_cell} |")
        else:
            print("| PWA | Download Link | Downloads |")
            print("| :--- | :--- | :--- |")
            for filepath in nro_files:
                filename = os.path.basename(filepath)
                pwa_name = os.path.splitext(filename)[0].replace("_", " ")
                download_url = f"https://github.com/{repo}/releases/download/{tag}/{filename}"
                badge_url = f"https://img.shields.io/github/downloads/{repo}/{tag}/{filename}?label=%20&style=flat-square&color=blue"
                print(f"| **{pwa_name}** | [{filename}]({download_url}) | ![{pwa_name} Downloads]({badge_url}) |")
        print("\n")

if __name__ == "__main__":
    main()
