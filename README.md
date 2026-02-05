# YouTube Music Mix Automation Tool 🎵🔥

An automated pipeline for creating and uploading high-quality YouTube music mixes with synchronized visuals and tracklists. This tool streamlines the entire process of channel management for music curation, supporting both web scraping and local assets.

## 🚀 Overview

This tool automates the lifecycle of a music curation channel:
1.  **Track Discovery**: Fetches tracks from Spotify or YouTube Music playlists.
2.  **Audio Downloading**: Automatically finds and downloads high-quality audio using `yt-dlp`.
3.  **Visual Assets**: Scrapes cinematic "Twixtor" clips or uses local video folders.
4.  **Audio/Video Mixing**: Merges tracks with visuals, adds transitions, and generates a timestamped tracklist using `MoviePy`.
5.  **YouTube Upload**: Handles metadata (titles, descriptions, tags) and uploads the final mix to your channel.

## ✨ Key Features

-   **Multi-Channel Management**: Independent profiles in `settings.yaml` for different niches (e.g., Phonk, Lo-fi, Gaming).
-   **Local & Web Visuals**: Use your own video folders or automatically scrape high-quality Twixtor clips.
-   **Smart Mixing**: Configurable mix duration, track limits, and clip selection.
-   **Dynamic Metadata**: Randomized title templates and automated description generation with timestamps.
-   **Scheduled Workflows**: Fully compatible with GitHub Actions for 24/7 automation.
-   **Persistent Auth**: Built-in flow to capture and reuse refresh tokens for seamless uploads.

## 🛠️ Tech Stack

-   **Language**: Python 3.11+
-   **Package Manager**: [uv](https://github.com/astral-sh/uv)
-   **Video Processing**: MoviePy
-   **Downloads**: yt-dlp, pytubefix, gdown
-   **APIs**: Google YouTube Data API v3, Spotify Web API, YouTube Music API
-   **CLI**: Typer

## 📋 Prerequisites

-   [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.
-   Google Cloud Project with **YouTube Data API v3** enabled.
-   `client_secrets.json` in the `config/` directory.
-   Spotify API credentials (optional, for Spotify playlists).

## ⚙️ Setup

1.  **Clone & Install**:
    ```bash
    git clone <repository-url>
    cd Youtube_Music_Mix-AG
    uv sync
    ```

2.  **Environment Variables**:
    Create a `.env` file:
    ```env
    SPOTIPY_CLIENT_ID='your_spotify_id'
    SPOTIPY_CLIENT_SECRET='your_spotify_secret'
    ```

3.  **Configuration**:
    Edit `config/settings.yaml` to define your channels. Use the `auth` command to add new channels interactively.

## 🎮 CLI Usage

### 1. Run Automation
The main command to fetch, download, mix, and upload.
```bash
uv run python main.py run --channel <name> [OPTIONS]
```
**Options:**
-   `--channel`: Channel profile to use (default: `primary`).
-   `--dry`: Perform a dry run (skip upload).
-   `--mix-minutes`: Override mix duration in minutes.
-   `--track-limit`: Limit the number of tracks fetched.
-   `--video-category`: Number of visual categories to use.
-   `--video-clips`: Number of clips per category.
-   `--posting`: Privacy status (`public`, `private`, `unlisted`).

### 2. Authenticate
Setup or refresh YouTube API tokens.
```bash
uv run python main.py auth --channel <name>
```
*Tip: After auth, the tool will provide a refresh token you can save in `settings.yaml` for persistent access.*

### 3. Scrape Twixtor Links
Export Google Drive links for cinematic visual clips.
```bash
uv run python main.py twixtor-links --num-series 5 --num-clips 10
```

## 📂 Project Structure

-   `main.py`: CLI entry point.
-   `src/app.py`: Core application logic and service orchestration.
-   `src/services/`:
    -   `music_provider.py`: Spotify and YT Music integration.
    -   `downloader.py`: Audio/Video extraction (`yt-dlp`).
    -   `mixer.py`: Video assembly and tracklist generation.
    -   `uploader.py`: YouTube Data API integration.
    -   `twixtor.py`: Visual asset scraping.
-   `config/`: YAML settings, secrets, and tokens.
-   `archive/`: Storage for completed mixes and logs.

## 📝 License

Distributed under the MIT License.
