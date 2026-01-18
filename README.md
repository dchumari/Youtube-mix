# YouTube Music Mix Automation

An automated tool to generate and upload music mixes to YouTube. It fetches tracks from Spotify playlists, downloads high-quality audio, pairs it with background visuals (anime twixtors, drive folders, or local clips), creates a seamless mix, and uploads it to YouTube with SEO-optimized metadata.

## Features

-   **Multi-Source Video Support**:
    -   **Twixtor**: Automatically scrapes compatible Twixtor sites for visuals.
    -   **Google Drive**: Downloads video backgrounds from a public Drive folder.
    -   **Local**: Uses your own local custom video clips.
-   **Spotify Integration**: Fetches tracks from any specified Spotify playlist.
-   **Automated Mixing**: Concatenates audio and loops/randomizes video clips to match duration.
-   **YouTube Uploading**: uploads the final mix with configurable Title, Description, and Tags.
-   **Multi-Channel Support**: Manage multiple YouTube channels from a single config file (e.g., "Primary", "Gaming").
-   **CLI Support**: Override sources and paths effortlessly via command-line arguments.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/youtube-music-mix.git
    cd youtube-music-mix
    ```

2.  **Install Dependencies**:
    Requires Python 3.9+.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `ffmpeg` is installed and added to your system PATH.*

3.  **Setup Configuration**:
    -   Copy `.env.example` to `.env` and fill in your Spotify API keys (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`).
    -   Place your YouTube OAuth `client_secrets.json` in `config/`.

## Configuration

Edit `config/settings.yaml` to customize channels and defaults.

### Channel Config Structure
```yaml
channels:
  primary:
    secrets_file: "config/client_secrets.json"
    token_file: "config/tokens/primary_token.json"
    playlist_id: "YOUR_SPOTIFY_PLAYLIST_ID"
    
    # Video Source Options
    video_provider: "twixtor" # or "drive", "local"
    # drive_url: "https://drive.google.com/..." # Required if provider is "drive"
    # local_video_path: "C:/MyVideos" # Required if provider is "local"
    
    tags: ["music", "mix"]
    description_template: "Mix Description here...\n{time_stamps}"
```

## Usage

### Basic Run
Run the automation for the default (primary) channel:
```bash
python main.py run
```

### Authentication
Run this once to generate your token file (opens browser login):
```bash
python main.py auth --channel primary
```

### CLI Overrides (Advanced)
You can force a specific video source without changing the config file.

**Use a Local Video Folder:**
```bash
python main.py run --source local --path "d:/Videos/AnimeClips"
```

**Use a Google Drive Folder:**
```bash
python main.py run --source drive --path "https://drive.google.com/drive/folders/1A2B3C..."
```

**Dry Run (Mix only, no upload):**
```bash
python main.py run --dry
```

## Directory Structure
-   `src/`: Main source code.
-   `config/`: Configuration files and secrets.
-   `downloads/`: Temporary download cache (cleaned up automatically).
-   `logs/`: Application logs.

## Video Sources Explained
-   **Twixtor**: Best for anime mixes. Scrapes clips from `animeworldtwixtor.com`.
-   **Drive**: Best for generic backgrounds. Provide a link to a folder containing MP4/MKV files. `gdown` will download them.
-   **Local**: Best for manually curated clips. Provide an absolute path to a folder on your machine.
