import os
import sys
import glob

def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "FaserF/pwa2nx")
    tag = sys.argv[1] if len(sys.argv) > 1 else "v1.0.0"
    
    nro_files = sorted(glob.glob("artifacts/*.nro"))
    
    if nro_files:
        print("### 🎮 Available PWAs in this Release\n")
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
