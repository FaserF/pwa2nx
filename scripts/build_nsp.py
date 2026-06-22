import sys
import os
import hashlib
import json
import subprocess
import glob


def generate_title_id(name: str) -> str:
    # Hash name and format as a valid homebrew Title ID: 05XXXXXXXXXXXXXX
    h = hashlib.sha256(name.encode()).hexdigest()
    # Use 14 hex chars from hash
    return f"05{h[:14].lower()}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python build_nsp.py <app_name> <safe_name>")
        sys.exit(1)

    app_name = sys.argv[1]
    safe_name = sys.argv[2]
    title_id = generate_title_id(app_name)

    print(f"Generating NSP for {app_name} with Title ID: {title_id}")

    # 1. Create build directories
    os.makedirs("nsp_build/exefs", exist_ok=True)
    os.makedirs("nsp_build/control", exist_ok=True)

    # 2. Compile npdm.json
    npdm_data = {
        "name": safe_name[:12],  # Max 12 chars
        "title_id": title_id,
        "main_thread_stack_size": 1048576,
        "main_thread_priority": 44,
        "default_cpu_id": 0,
        "process_category": 0,
        "is_retail": True,
        "pool_partition": 2,
        "is_aslr_enabled": True,
        "address_space_type": 3,
        "filesystem_access": {"permissions": "0xffffffffffffffff"},
        "service_access": ["*"],
        "kernel_capabilities": [
            {
                "type": "syscalls",
                "value": {
                    "0": "0xffffffff",
                    "1": "0xffffffff",
                    "2": "0xffffffff",
                    "3": "0xffffffff",
                    "4": "0xffffffff",
                    "5": "0xffffffff",
                    "6": "0xffffffff",
                    "7": "0xffffffff",
                },
            }
        ],
    }

    with open("nsp_build/npdm.json", "w") as f:
        json.dump(npdm_data, f, indent=2)

    # Run npdmtool to compile main.npdm
    subprocess.run(
        ["npdmtool", "nsp_build/npdm.json", "nsp_build/exefs/main.npdm"], check=True
    )

    # 3. Strip ELF to exefs/main
    subprocess.run(
        ["aarch64-none-elf-strip", "-o", "nsp_build/exefs/main", "pwa2nx.elf"],
        check=True,
    )

    # 4. Copy NACP file
    if os.path.exists("pwa2nx.nacp"):
        subprocess.run(
            ["cp", "pwa2nx.nacp", "nsp_build/control/control.nacp"], check=True
        )
    else:
        # Fallback build nacp
        subprocess.run(
            [
                "nacptool",
                "--create",
                app_name,
                "FaserF",
                "1.0.0",
                "nsp_build/control/control.nacp",
            ],
            check=True,
        )

    # 5. Convert icon to JPEG and place as icon_AmericanEnglish.dat
    if os.path.exists("source/icon.jpg"):
        subprocess.run(
            ["cp", "source/icon.jpg", "nsp_build/control/icon_AmericanEnglish.dat"],
            check=True,
        )

    # 6. Check for keys
    has_keys = (
        os.path.exists(os.path.expanduser("~/.switch/prod.keys"))
        or os.path.exists("prod.keys")
        or os.path.exists("keys.dat")
    )

    hacbrewpack_cmd = ["hacbrewpack", "--nspdir", ".", "--nopatch"]
    if not has_keys:
        print(
            "Warning: Keys not found. Generating plaintext (unencrypted) NSP fallback..."
        )
        hacbrewpack_cmd.append("--plaintext")

    # Run hacbrewpack
    # hacbrewpack expects build files in a folder, let's create a root folder containing exefs/control
    os.makedirs("nsp_root", exist_ok=True)
    subprocess.run(["cp", "-r", "nsp_build/exefs", "nsp_root/"], check=True)
    subprocess.run(["cp", "-r", "nsp_build/control", "nsp_root/"], check=True)

    hacbrewpack_cmd.extend(["--rootdir", "nsp_root"])

    # Run hacbrewpack
    subprocess.run(hacbrewpack_cmd, check=True)

    # Find the output .nsp file and rename it to safe_name.nsp
    generated_nsps = glob.glob("*.nsp")
    if generated_nsps:
        os.rename(generated_nsps[0], f"{safe_name}.nsp")
        print(f"Successfully generated NSP: {safe_name}.nsp")
    else:
        print("Error: NSP was not generated.")
        sys.exit(1)


if __name__ == "__main__":
    main()
