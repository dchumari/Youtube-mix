import glob
import json
import random
from datetime import datetime
from pathlib import Path

# Get the directory where this script is located
p = Path(__file__).parent.resolve()

year = datetime.now().strftime("%Y")

profiles = p / "profiles"
thumbnails_folder = p / "thumbnails"


def get_profiles(path):
    with open(path, "r", encoding="utf-8") as f:
        content = json.load(f)
        return content


# Define your possible video titles
def video_metadata(channel_name, time_stamps=None):
    profile = profiles / f"{channel_name}.json"
    profile.resolve()
    details = get_profiles(profile)

    thumbnails_dir = thumbnails_folder / channel_name

    if not thumbnails_dir.exists():
        raise FileNotFoundError(f"Thumbnails folder not found for {channel_name}!")

    thumbnail_files = (
        list(thumbnails_dir.glob("*.[jJ][pP][eE][gG]"))
        + list(thumbnails_dir.glob("*.[jJ][pP][gG]"))
        + list(thumbnails_dir.glob("*.[pP][nN][gG]"))
    )

    if not thumbnail_files:
        raise FileNotFoundError(f"No thumbnails found in {thumbnails_dir}!")

    thumbnail = random.choice(thumbnail_files).resolve()

    return {
        "title": random.choice(details["title"]).format(year=year),
        "description": details["description_template"].format(time_stamps=time_stamps),
        "tags": details["tags"],
        "category": details["category"],
        "privacy": details["privacy"],
        "thumbnail": details["thumbnail"].format(thumbnail=thumbnail),
        "made_for_kids": details["made_for_kids"],
    }


if __name__ == "__main__":
    time_stamps = "00:00\n 01:00\n 02:00"

    print(video_metadata("phonkmixxx", time_stamps=time_stamps))
