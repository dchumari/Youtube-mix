import typer
import yaml
from pathlib import Path
from src.app import App
from src.utils.logger import logger

app = typer.Typer(help="YouTube Music Mix Automation Tool")

@app.command()
def run(
    channel: str = typer.Option("primary", help="Channel profile to use (defined in settings.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Skip upload step"),
    mix_minutes: int = typer.Option(None, "--mix-minutes", help="Duration of the mix in minutes"),
    track_limit: int = typer.Option(None, "--track-limit", help="Maximum number of tracks to fetch"),
    video_category: int = typer.Option(None, "--video-category", help="Number of series categories for Twixtor"),
    video_clips: int = typer.Option(None, "--video-clips", help="Number of clips per category or total clips"),
    posting: str = typer.Option(None, "--posting", help="Privacy status (public/private/unlisted)"),
    video_folders: str = typer.Option(None, "--video-folders", help="Google Drive link or ID for visuals")
):
    """
    Runs the full automation workflow: Fetch -> Download -> Mix -> Upload.
    """
    try:
        bot = App(
            channel_profile=channel,
            mix_minutes=mix_minutes,
            track_limit=track_limit,
            video_category=video_category,
            video_clips=video_clips,
            posting=posting,
            video_folders=video_folders
        )
        bot.run(dry_run=dry)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(code=1)

@app.command()
def twixtor_links(
    channel: str = typer.Option("primary", help="Channel profile to use for settings (download folder etc)"),
    num_series: int = typer.Option(5, help="Number of series categories to scrape"),
    num_clips: int = typer.Option(5, help="Number of clips to scrape in total")
):
    """
    Scrapes and prints Google Drive links for Twixtor clips.
    """
    try:
        bot = App(channel_profile=channel)
        links = bot.get_twixtor_links(num_series=num_series, num_clips=num_clips)
        if links:
            print("\n--- Twixtor Drive Links ---")
            for link in links:
                print(link)
            print("---------------------------\n")
        else:
            logger.warning("No links found.")
    except Exception as e:
        logger.error(f"Failed to get links: {e}")
        raise typer.Exit(code=1)

@app.command()
def auth(
    channel: str = typer.Option("primary", help="Channel profile to authenticate")
):
    """
    Runs the authentication flow for a specific channel.
    This opens a browser to save the token.
    """
    try:
        ensure_channel_exists(channel)
        bot = App(channel_profile=channel)
        bot.auth_only()
        
        # After successful auth, find and print the refresh token if available
        if bot.uploader.token_file.exists():
            import json
            with open(bot.uploader.token_file, "r") as f:
                token_data = json.load(f)
                refresh_token = token_data.get("refresh_token")
                if refresh_token:
                    # Automatically save to settings.yaml
                    update_refresh_token_in_config(channel, refresh_token)
                    
                    print("\n" + "="*50)
                    print("SUCCESS! Your refresh token has been automatically saved")
                    print(f"to settings.yaml for channel '{channel}'.")
                    print(f"\nRefresh Token: {refresh_token}\n")
                    print("="*50 + "\n")
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise typer.Exit(code=1)

@app.command()
def delete_channel(
    channel: str = typer.Argument(..., help="Name of the channel profile to delete")
):
    """
    Deletes a channel profile from settings.yaml.
    """
    config_path = "config/settings.yaml"
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise typer.Exit(code=1)

    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    if "channels" not in config or channel not in config["channels"]:
        logger.error(f"Channel '{channel}' not found.")
        raise typer.Exit(code=1)

    confirm = typer.confirm(f"Are you sure you want to delete the profile for '{channel}'?")
    if confirm:
        del config["channels"][channel]
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, sort_keys=False, allow_unicode=True)
        logger.info(f"Successfully deleted channel '{channel}' from {config_path}")
    else:
        logger.info("Deletion cancelled.")

def ensure_channel_exists(channel: str, config_path: str = "config/settings.yaml"):
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise typer.Exit(code=1)
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    if "channels" not in config:
        config["channels"] = {}
        
    if channel not in config["channels"]:
        confirm = typer.confirm(f"Channel '{channel}' not found in settings.yaml. Is it a new channel you want to add?")
        if confirm:
            create_new_channel_profile(channel, config, config_path)
        else:
            logger.error(f"Profile '{channel}' not found and creation skipped.")
            raise typer.Exit(code=1)

def create_new_channel_profile(channel: str, config: dict, config_path: str):
    logger.info(f"Setting up new channel profile: {channel}")
    
    secrets_file = typer.prompt("Path to client_secrets.json", default="config/client_secrets.json")
    token_file = typer.prompt(f"Path to save token JSON", default=f"config/tokens/{channel}_token.json")
    youtube_channel_name = typer.prompt("YouTube Channel Name")
    playlist_id = typer.prompt("Spotify Playlist ID")
    tags_str = typer.prompt("Tags (comma separated)", default="music, mix")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    
    title_templates = []
    print("\nEnter Title Templates (leave empty to finish):")
    while True:
        template = typer.prompt(f"Title template {len(title_templates) + 1}", default="", show_default=False)
        if not template:
            break
        title_templates.append(template)
        
    if not title_templates:
        title_templates = [f"Best Music Mix 2025 - {channel.title()} 🎵"]

    description_template = typer.prompt(
        "Description Template (use {time_stamps} for tracklist)", 
        default="Enjoy this mix!\n\n{time_stamps}"
    )

    posting = typer.prompt("Privacy Status (public, private, unlisted)", default="private")
    mix_minutes = typer.prompt("Mix Duration (minutes)", default=3, type=int)
    track_limit = typer.prompt("Track Limit", default=10, type=int)
    video_category = typer.prompt("Video Category (number of series)", default=2, type=int)
    video_clips = typer.prompt("Video Clips (number per group)", default=5, type=int)
    video_folders = typer.prompt("Video Folders (Google Drive link, leave empty to use scraper)", default="")
    thumbnail_folders = typer.prompt("Thumbnail Folders (Google Drive link, leave empty to skip)", default="")
    refresh_token = typer.prompt("Manual Refresh Token (leave empty to skip)", default="")

    config["channels"][channel] = {
        "secrets_file": secrets_file,
        "token_file": token_file,
        "youtube_channel_name": youtube_channel_name,
        "playlist_id": playlist_id,
        "tags": tags,
        "posting": posting,
        "mix_minutes": mix_minutes,
        "track_limit": track_limit,
        "video_category": video_category,
        "video_clips": video_clips,
        "video_folders": video_folders,
        "thumbnail_folders": thumbnail_folders,
        "refresh_token": refresh_token,
        "title_templates": title_templates,
        "description_template": description_template
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Successfully added channel '{channel}' to {config_path}")


def update_refresh_token_in_config(channel: str, refresh_token: str, config_path: str = "config/settings.yaml"):
    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found for update: {config_path}")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    if "channels" in config and channel in config["channels"]:
        config["channels"][channel]["refresh_token"] = refresh_token
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, sort_keys=False, allow_unicode=True)
        logger.info(f"Updated 'refresh_token' for channel '{channel}' in {config_path}")
    else:
        logger.warning(f"Channel '{channel}' not found in {config_path}, skipping refresh_token update.")


if __name__ == "__main__":
    app()
