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
    The tool uses `config/settings.yaml` to manage multiple channels. You can edit this file manually or use the `auth` command to help validatsetup.

## ⚙️ Configuration Guide

The `config/settings.yaml` file is the heart of the automation. You can define multiple channel profiles (e.g., `primary`, `gaming`, `lofi`) with unique settings.

### Channel Profile Options

| Option                 | Description                                            | Example                         |
| :--------------------- | :----------------------------------------------------- | :------------------------------ |
| `secrets_file`         | Path to your Google OAuth client secrets.              | `config/client_secrets.json`    |
| `token_file`           | Path where the authenticated token will be saved.      | `config/tokens/token.json`      |
| `playlist_id`          | Spotify Playlist ID to source music from.              | `3mAH5gPbw4...`                 |
| `video_folders`        | Google Drive link(s) for video clips. String or List.  | `https://drive.google.com...`   |
| `thumbnail_folders`    | Google Drive link(s) for thumbnails.                   | `https://drive.google.com...`   |
| `mix_minutes`          | Target duration of the final mix in minutes.           | `15`                            |
| `track_limit`          | Maximum number of tracks to fetch/download.            | `20`                            |
| `posting`              | Privacy status of the uploaded video.                  | `public`, `private`, `unlisted` |
| `tags`                 | List of YouTube tags.                                  | `['music', 'mix', '2025']`      |
| `title_templates`      | List of templates for generating video titles.         | `['Late Night Vibes 🌑']`        |
| `description_template` | Template for description. Use `{time_stamps}`.         | `Enjoy!\n\n{time_stamps}`       |
| `video_category`       | (Twixtor) Number of anime/series categories to search. | `3`                             |
| `video_clips`          | (Twixtor) Number of clips to download per category.    | `5`                             |
| `refresh_token`        | (Optional) Saved refresh token for auto-auth.          | `1//0e...`                      |

### Example `settings.yaml` structure

```yaml
defaults:
  mix_minutes: 10
  posting: private

channels:
  primary:
    secrets_file: config/client_secrets.json
    playlist_id: 3mAH5gPbw4...
    video_folders: 
      - https://drive.google.com/drive/folders/ID_1
      - https://drive.google.com/drive/folders/ID_2
    posting: public
    title_templates: 
      - "Best Music Mix 2025 🎧"
    description_template: |
      Check out this mix!
      
      Tracklist:
      {time_stamps}
```

## 🎮 CLI Usage

### 1. Run Automation (`run`)
The main command to fetch, download, mix, and upload.

```bash
uv run python main.py run --channel <name> [OPTIONS]
```

**Options:**
-   `--channel`: Channel profile to use (default: `primary`).
-   `--dry`: Perform a dry run (skips upload).
-   `--mix-minutes`: Override mix duration in minutes.
-   `--track-limit`: Limit the number of tracks fetched.
-   `--video-category`: Number of visual categories to use (Twixtor).
-   `--video-clips`: Number of clips per category.
-   `--video-folders`: Override video source with a specific Google Drive link or ID.
-   `--posting`: Override privacy status (`public`, `private`, `unlisted`).

### 2. Authenticate (`auth`)
Setup or refresh YouTube API tokens. This opens a browser to grant permissions.

```bash
uv run python main.py auth --channel <name>
```
*Tip: After auth, the tool allows you to save the refresh token to `settings.yaml` for persistent, headless access.*

### 3. Visual Utilities (`twixtor-links`)
Export Google Drive links for cinematic visual clips to use in your `video_folders`.

```bash
uv run python main.py twixtor-links --num-series 5 --num-clips 10
```

### 4. Management (`delete-channel`)
Delete a channel profile from your settings.

```bash
uv run python main.py delete-channel <name>
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
