import glob
import json
import os
import random
import time
from pathlib import Path
from typing import Literal

import spotipy
import yt_dlp
from dotenv import load_dotenv
from pytubefix import YouTube
from pytubefix.cli import on_progress
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic
from ytmusicapi.parsers.podcasts import P

from .file_manager import clean_up

# from delete import delete_mp4
from .mix import make_custom_mix, make_mix
from .twixtors import get_anime_clips
from .upload_to_youtube import get_authenticated_service, upload_video

# from .youtube_utils import TAGS, THUMBNAIL, TITLE, description
from .youtube_utils_copy import video_metadata

load_dotenv()
ym = YTMusic()

path = Path(__file__).parent
DOWNLOAD_PATH = path.parent / "downloads"
DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_spotify_client():
    client_id = SPOTIFY_CLIENT_ID
    client_secret = SPOTIFY_CLIENT_SECRET
    return spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )


def dump(x):
    print(json.dumps(x, indent=4))


sp = get_spotify_client()


# def download_media(url, path, type: Literal["video", "audio"]):
#     if type == "audio":
#         quality = "bestaudio"
#         extension = "mp3"
#     elif type == "video":
#         quality = "bestvideo+bestaudio/best"
#         extension = "mp4"
#     else:
#         raise ValueError(f"Invalid type: {type}")

#     ydl_opts = {
#         "outtmpl": f"{path}/%(title)s.%(ext)s",
#         "format": quality,
#         "postprocessors": [
#             {"key": "FFmpegVideoConvertor", "preferedformat": extension}
#         ],
#         "postprocessor_args": {"ffmpeg": ["-c", "copy"]},
#         "quiet": False,
#         "progress": True,
#         # CRITICAL: Tell yt-dlp to skip the web_safari formats that cause SABR issues
#         "extractor_args": {
#             "youtube": {
#                 "player_client": ["android", "web"],
#                 "formats": ["incomplete"],
#             }
#         },
#     }

#     max_retries = 3
#     for attempt in range(max_retries):
#         try:
#             with YoutubeDL(ydl_opts) as ydl:
#                 ydl.download([url])
#             break  # Success, exit loop
#         except Exception as e:
#             print(f"Download attempt {attempt + 1} failed: {e}")
#             if attempt == max_retries - 1:
#                 print(f"Failed to download {url} after {max_retries} attempts.")
#                 raise  # Re-raise the last error
#             time.sleep(2)  # Wait before retrying


def download_media(url, path, type: Literal["video", "audio"]):
    if type == "audio":
        ydl_opts = {
            "outtmpl": f"{path}/%(title)s.%(ext)s",
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": False,
        }

    elif type == "video":
        ydl_opts = {
            "outtmpl": f"{path}/%(title)s.%(ext)s",
            # ✅ SAFE FORMAT (no SABR, no PO token)
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": False,
        }

    else:
        raise ValueError(f"Invalid type: {type}")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return
        except Exception as e:
            print(f"Download attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)


def download_from_pytube(
    url,
    path,
):
    yt = YouTube(url, on_progress_callback=on_progress)
    print(yt.title)

    ys = yt.streams.filter(
        progressive=True, file_extension="mp4", resolution="1080p"
    ).first()

    if ys:
        print("Downloading...")
        ys.download(output_path=path)


def spotify_mixer(
    youtube_channel_name,
    client_secrets,
    playlist_id,
    mix_minutes,
    track_limit,
    mix_type="default",
    video_folder=None,
    video_category=5,
    video_clips=5,
):
    if mix_type not in ("default", "custom"):
        raise ValueError("Invalid mix type")

    playlist = sp.playlist(playlist_id)
    if not playlist:
        raise ValueError("Playlist not found")
    # dump(playlist)

    playlist_items = sp.playlist_items(playlist_id, limit=100)
    if not playlist_items:
        raise ValueError("Playlist items not found")
    # dump(playlist_items)

    playlist_name = "_".join(playlist.get("name").split()[:3])
    playlist_items = playlist_items.get("items")

    random.shuffle(playlist_items)
    # dump(playlist_items)

    tracks = []
    for item in playlist_items:
        item.get("track").pop("available_markets")
        item.get("track").get("album").pop("available_markets")
        tracks.append(item.get("track"))

    tracks = tracks[:track_limit]
    # print(len(tracks))
    # dump(tracks)

    total_duration = sum(track.get("duration_ms") for track in tracks) / 60000
    print(f"\nTotal duration: {total_duration:.2f} minutes")

    while total_duration > mix_minutes:
        tracks.pop()
        total_duration = sum(track.get("duration_ms") for track in tracks) / 60000

    print(f"Total duration: {total_duration:.2f} minutes")

    # GET FROM YOUTUBE
    print("\n==================== Getting details from YouTube ====================")

    playlist_folder = DOWNLOAD_PATH / playlist_name
    playlist_folder.mkdir(parents=True, exist_ok=True)

    id = 0
    for track in tracks:
        track_name = track.get("name")
        artist_name = track.get("artists")[0].get("name")

        search_query = f"{track_name} {artist_name}"
        # print(f"Search info of: {search_query}")
        search_results = ym.search(search_query, filter="songs")[0]
        video_id = search_results.get("videoId")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        track["video_url"] = video_url
        track["id"] = id
        id += 1

        try:
            print("\n==================== Downloading with YTDLP ====================")
            if mix_type == "default":
                download_media(video_url, playlist_folder, type="video")
            elif mix_type == "custom":
                download_media(video_url, playlist_folder, type="audio")
        except Exception as e:
            print(f"\nFailed to download video with yt-dlp: {video_url}")
            print(f"\nError: {e}")

    if not video_folder:
        print("\nNo video folder specified. using default")
        video_folder = DOWNLOAD_PATH / "twixtors"
        video_folder.mkdir(parents=True, exist_ok=True)
        get_anime_clips(animes_series=video_category, anime_clips=video_clips)

    if mix_type == "default":
        result = make_mix(playlist_folder)
    elif mix_type == "custom":
        result = make_custom_mix(playlist_folder, video_folder=video_folder)
    else:
        raise ValueError("Invalid mix type")

    if not result:
        print("Failed to create mix.")
        exit(1)

    timestamps, output_file = result

    if isinstance(timestamps, list):
        print("\nMix created successfully!")

        # Give a tiny extra breath + ensure clips are closed
        time.sleep(3)

        print("Cleaning up... playlist")
        clean_up(playlist_folder, extension="mp3")
        clean_up(playlist_folder, extension="mp4")

        print("Cleaning up... twixtors")
        clean_up(video_folder, extension="mp4")
    else:
        print("\nFailed to create mix.")

    # UPLOAD TO YOUTUBE
    print("\n==================== Uploading to YouTube ====================")

    time_stamps = "\n".join(timestamps)
    # des = description(time_stamps)
    data = video_metadata(youtube_channel_name, time_stamps)
    print(data)

    youtube = get_authenticated_service(
        youtube_channel_name, client_secrets_file_name=client_secrets
    )
    upload_video(
        youtube=youtube,
        video_file=output_file,
        title=data["title"],
        description=data["description"],
        tags=data["tags"],
        thumbnail=data["thumbnail"],
    )


if __name__ == "__main__":
    spotify_mixer("phonkmixxx", "client_secrets.json")
