import os
import shutil
from pathlib import Path

# Use the path provided by the user as base
ROOT = Path(r"D:\ClawAI")
source_dir = ROOT / "clawaii"
target_dir = ROOT / "clawai"

def consolidate():
    print(f"Consolidating {source_dir} into {target_dir}...")
    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist.")
        return

    # 1. Move folders that don't exist in target yet
    for item in source_dir.iterdir():
        if item.name.startswith(".") or item.name == ".env":
            continue
            
        dest = target_dir / item.name
        if not dest.exists():
            print(f"Copying new folder/file: {item.name}")
            try:
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            except Exception as e:
                print(f"Failed to copy {item.name}: {e}")

    # 2. Handle conflicts (autonomy, cognition, core)
    conflicts = ["autonomy", "cognition", "core"]
    for folder_name in conflicts:
        src_folder = source_dir / folder_name
        dest_folder = target_dir / folder_name
        if src_folder.exists() and dest_folder.exists():
            print(f"Merging conflict directory: {folder_name}")
            # We want to keep the richer content from clawai (the current one) 
            # but also take anything unique from clawaii?
            for item in src_folder.iterdir():
                sub_dest = dest_folder / item.name
                if not sub_dest.exists() and (item.is_file() or item.is_dir()):
                    try:
                        if item.is_dir():
                            shutil.copytree(item, sub_dest)
                        else:
                            shutil.copy2(item, sub_dest)
                    except Exception as e:
                        print(f"Failed to merge {folder_name}/{item.name}: {e}")

    print("Consolidation complete.")

if __name__ == "__main__":
    consolidate()