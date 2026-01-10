import glob
import random
from datetime import datetime
from pathlib import Path

# Get the directory where this script is located
p = Path(__file__).parent.resolve()

year = datetime.now().strftime("%Y")

# Define your possible video titles
TITLES = [
    f"AURA = ♾️ | TOP 10 BRAZILIAN PHONK MIX PLAYLIST {year}",
    f"BEST BRAZILIAN PHONK MIX PLAYLIST {year}",
    f"AURA = | BRAZILIAN MUSIC PLAYLIST MIX {year}",
    f"THE ULTIMATE BRAZILIAN PHONK MIX {year} 🔥‼️ | 𝘪𝘯 𝘚𝘭𝘰𝘸𝘸𝘦𝘥 𝘢𝘯𝘥 𝘙𝘦𝘷𝘦𝘳𝘣 ⚡‼️",
    f"AURA = ♾️ | BRAZILIAN PHONK MIX {year} ",
    f"AURA BRAZILIAN PHONK MIX COMPILATION | Montagem, Eternxl | Gym Drift {year}",
    f"TOP 10 MOST VIRAL PHONK/FUNK {year} | Slowed + Reverb + Brazilian Bass 🎵",
]

# Path to your thumbnails folder (relative to this script)
thumbnails_dir = p / "THUMBNAILS" / "THE_PHONK_MIX"

# Get all .jpeg and .jpg files (case-insensitive) thumbnails
thumbnail_files = (
    list(thumbnails_dir.glob("*.[jJ][pP][eE][gG]"))
    + list(thumbnails_dir.glob("*.[jJ][pP][gG]"))
    + list(thumbnails_dir.glob("*.[pP][nN][gG]"))
)

if not thumbnail_files:
    raise FileNotFoundError(f"No thumbnails found in {thumbnails_dir}!")

# Randomly select one thumbnail
THUMBNAIL = random.choice(thumbnail_files)

# Random title
TITLE = random.choice(TITLES)

# DESCRIPTION


def description(time_stamps):
    des = f"""
MIX OF THE SUPREME BRAZILIAN PHONK 2025 | Slowed + Reverb + Brazilian Bass 🎵

🎧 YOUR ULTIMATE PHONK SESSION STARTS HERE 🎧

Prepare for a non-stop wave of the hardest, most hypnotic Brazilian Phonk anthems of 2025. This mix is engineered for maximum impact — blending crushing bass, iconic vocal samples, and those signature slowed & reverb drops that define the genre. From the dark vibes of `MONTAGEM RUGADA` to the aggressive energy of `AL NACER`, this is a curated journey through the underground sound dominating the scene. Crank it up and let the phonk take control. 🔥🇧🇷

👀 TRACKLIST:
{time_stamps}

📜 COPYRIGHT DISCLAIMER:
All tracks and visuals belong to their respective owners.
No copyright infringement intended — this video is for promotional and entertainment purposes only.
If you are the owner and wish to remove or modify credits, please contact me.

Tags:
supreme phonk, brazilian phonk 2025, phonk mix 2025, slowed and reverb phonk, hard phonk, montagem 2025, phonk brasileiro, aggressive phonk, phonk compilation, phonk edit, phonk workout, driving phonk, underground phonk, phonk br, phonk tiktok, funk phonk, best phonk mix, phonk playlist, phonk music, phonk songs, aura phonk

#phonk #phonkmix #brazilianphonk #montagem #phonk2025 #funk #slowedandreverb #phonkmusic #phonkbr #hardphonk
    """
    return des


DESCRIPTION = "This is a description for the video."

# Optional: Add timestamp or uniqueness
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("Selected Thumbnail:", THUMBNAIL)
print("Selected Title:", TITLE)
print("Suggested Filename:", f"phonk_mix_{timestamp}.mp4")

TAGS = [
    "brazilian phonk",
    "phonk brasileiro",
    "brazilian phonk mix",
    "phonk mix 2024",
    "new phonk mix",
    "drift phonk",
    "phonk edit",
    "best phonk",
    "gym phonk",
    "training phonk",
    "motivation phonk",
    "phonk workout",
    "phonk for gym",
    "underground phonk",
    "phonk remix",
    "reverb phonk",
    "cowbell phonk",
    "phonk 808",
    "phonk bass",
    "wave phonk",
    "royalty free phonk",
    "1 hour phonk",
    "night drive phonk",
    "phonk playlist",
    "youtube phonk mix",
    "brazil music",
    "phonk nacional",
]
