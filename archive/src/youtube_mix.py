# YouTube_Music_Mix master

## 1
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict

from pytubesearch import PyTubeSearch
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

# Make the parent directory available for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from models directory
from find_trending import (
    debug_trending_calculation,
    find_trending_videos,
    find_trending_videos_days,
)
from mix import calculate_duration, make_mix
from trending_score import sort_by_trending_score

path = Path(__file__).parent
DOWNLOAD_PATH = path.parent / "downloads"
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

# Initialize the client
ys = PyTubeSearch()  # Fixed typo: PyTubeSearch → PytubeSearch
yt = YTMusic()


def song_info(song_id):
    song_info = yt.get_song(song_id)
    video_details = song_info.get("videoDetails", {})
    last_modified = (
        song_info.get("streamingData", {}).get("formats", [{}])[0].get("lastModified")
    )
    video_details["lastModified"] = last_modified
    return video_details


def download_video(url, path, score):
    ydl_opts = {
        "outtmpl": f"{path}/{score}_%(title)s.%(ext)s",
        # Just get the best format and let yt-dlp handle conversion
        "format": "best",
        # This will convert to MP4 if needed
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        # Optional: add FFmpeg args for better quality
        "postprocessor_args": {
            "ffmpeg": ["-c", "copy"]  # Try to copy without re-encoding first
        },
        "quiet": False,
        "progress": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def dump(q):
    print(json.dumps(q, indent=4))


def main(playlist_name, top_n=10, mix_minutes=14):
    #  SEARCH STEP
    search = yt.search(query=playlist_name, filter="playlists")

    playlist = random.choice(search)

    playlist_id = playlist.get("browseId", {})[2:]

    playlist_info = yt.get_playlist(playlist_id)

    tracksOld = playlist_info.pop("tracks")
    random.shuffle(tracksOld)

    tracksNew = []
    for track in tracksOld:
        video_id = track.get("videoId")
        video_details = song_info(video_id)
        tracksNew.append(video_details)

    playlist_info["tracks"] = tracksNew

    # SORTING BY UPLOADED DATE AND VIEWS

    # sorted_tracks = sort_by_trending_score(playlist_info, top_n=top_n)
    sorted_tracks = find_trending_videos(playlist_info, top_n=top_n)
    # sorted_tracks2 = find_trending_videos_days(playlist_info, top_n=top_n)

    # debug_trending_calculation(playlist_info)

    # dump(sorted_tracks)
    # print("__" * 100)

    # print(playlist_info)

    # LIMIT MINUTES

    total_minutes = calculate_duration(sorted_tracks)

    while total_minutes > mix_minutes:
        sorted_tracks.get("tracks").pop(0)
        total_minutes = calculate_duration(sorted_tracks)

    dump(sorted_tracks)

    # DOWNLOAD STEP

    playlist_title = sorted_tracks.get("title", "Unknown Playlist").split()[:3]
    playlist_title = "_".join(playlist_title)

    playlist_folder = DOWNLOAD_PATH / playlist_title
    playlist_folder.mkdir(parents=True, exist_ok=True)

    for track in sorted_tracks.get("tracks"):
        video_id = track.get("videoId")
        if not video_id:
            continue
        url = f"youtube.com/watch?v={video_id}"

        score = int(track.get("trendingScore", 0))

        download_video(url, playlist_folder, score=score)

    # MAKE THE MIX
    if make_mix(playlist_folder):
        print("\nMix created successfully!")
    else:
        print("\nMix creation failed.")

    # UPLOAD TO YOUTUBE


if __name__ == "__main__":
    main("Brazilian PHONK")
    # dump(song_info("B9KFb_fmvV8"))

    # print(ys.get_video_details("B9KFb_fmvV8").model_dump_json(indent=4))
