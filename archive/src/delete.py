import os
from pathlib import Path

from send2trash import send2trash


def delete_mp4(folder_path, really_delete=False):
    """
    Safely delete MP4 files.
    Set really_delete=False to move to trash (safer).
    Set really_delete=True for permanent deletion.
    """
    folder = Path(folder_path)

    # Find all MP4 files (case-insensitive)
    mp4_files = []
    for file_path in folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".mp4":
            mp4_files.append(file_path)

    if not mp4_files:
        return "No MP4 files found."

    # Process files
    for file_path in mp4_files:
        if really_delete:
            file_path.unlink()  # Permanent
        else:
            send2trash(str(file_path))  # To trash

    action = "Deleted" if really_delete else "Moved to trash"
    return f"{action} {len(mp4_files)} MP4 files."


if __name__ == "__main__":
    # Safer: Move to trash
    result = delete_mp4("E:/Videos", really_delete=False)

    print(result)

# Only use this if you're absolutely sure!
# result = safe_delete_mp4("E:/Videos", really_delete=True)
