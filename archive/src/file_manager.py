import glob
from pathlib import Path
from typing import Literal


def clean_up(folder_path, extension: Literal["mp4", "mp3"] = "mp4"):
    print(f"Cleaning up original .{extension} files...")
    deleted_count = 0
    for file in Path(folder_path).glob(f"*.{extension}"):
        try:
            file.unlink()
            deleted_count += 1
        except PermissionError as e:
            print(f"Could not delete {file.name}: {e}")
        except Exception as e:
            print(f"Unexpected error deleting {file.name}: {e}")

    print(f"\nCleaned up {deleted_count} original files.")
