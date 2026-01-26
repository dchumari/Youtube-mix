# YouTube Music Mix Automation Tool 🎵🔥

An automated pipeline for creating and uploading high-quality YouTube music mixes (e.g., Brazilian Phonk, Gaming OSTs) with synchronized visuals and tracklists.

## 🚀 Overview

This tool automates the entire process of channel management for music curation:
1.  **Track Discovery**: Fetches tracks from Spotify or YouTube Music playlists.
2.  **Audio Downloading**: Automatically finds and downloads the best quality audio for each track.
3.  **Visual Scraper**: Scrapes and downloads relevant "Twixtor" or cinematic clips for visuals.
4.  **Audio/Video Mixing**: Merges audio tracks with visuals, adds transitions, and generates a timestamped tracklist.
5.  **YouTube Upload**: Handles metadata (titles, descriptions, tags) and uploads the final mix directly to your YouTube channel.

## ✨ Key Features

-   **Multi-Channel Support**: Manage multiple YouTube channels with independent profiles in `settings.yaml`.
-   **Twixtor Integration**: Automated scraping of high-quality visuals to match the music vibe.
-   **Dynamic Metadata**: Randomly selects titles from templates and generates detailed descriptions with timestamps.
-   **GitHub Actions Ready**: Run your entire channel on autopilot using scheduled workflows.
-   **Reliable Downloads**: Powered by `yt-dlp` for robust audio and video extraction.
-   **Smart Cleanup**: Automatically removes temporary files to save disk space.

## 🛠️ Tech Stack

-   **Language**: Python 3.11+
-   **Package Manager**: [uv](https://github.com/astral-sh/uv)
-   **Video Processing**: MoviePy
-   **Downloads**: yt-dlp, pytubefix
-   **APIs**: Google YouTube Data API, Spotify Web API, YouTube Music API
-   **CLI**: Typer

## 📋 Prerequisites

-   [uv](https://docs.astral.sh/uv/getting-started/installation/) installed.
-   Google Cloud Project with **YouTube Data API v3** enabled.
-   `client_secrets.json` downloaded from Google Cloud Console.
-   (Optional) Spotify API credentials if using Spotify playlists.

## ⚙️ Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd Youtube_Music_Mix-AG
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

3.  **Configure Environment**:
    Create a `.env` file and add your credentials:
    ```env
    SPOTIPY_CLIENT_ID='your_id'
    SPOTIPY_CLIENT_SECRET='your_secret'
    # Other secrets as needed
    ```

4.  **Configure Settings**:
    Edit `config/settings.yaml` to define your channels, playlist IDs, and title/description templates.

5.  **Authenticate**:
    Run the authentication flow for your channel (this will open a browser):
    ```bash
    uv run python main.py auth --channel primary
    ```

## 🎮 Usage

### Run Automation
To fetch, download, mix, and upload:
```bash
uv run python main.py run --channel primary
```

### Dry Run (Skip Upload)
To test the mixing process without uploading to YouTube:
```bash
uv run python main.py run --channel primary --dry
```

### Authentication Only
To refresh or setup tokens:
```bash
uv run python main.py auth --channel primary
```

## 📂 Project Structure

-   `src/app.py`: Main application logic and service orchestration.
-   `src/services/`: Modular services for downloading, mixing, uploading, and scraping.
-   `config/`: YAML settings and API tokens.
-   `main.py`: CLI entry point.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
