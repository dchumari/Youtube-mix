import typer
import yaml
from pathlib import Path
from src.app import App
from src.utils.logger import logger

app = typer.Typer(help="YouTube Music Mix Automation Tool")

@app.command()
def run(
    channel: str = typer.Option("primary", help="Channel profile to use (defined in settings.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Skip upload step")
):
    """
    Runs the full automation workflow: Fetch -> Download -> Mix -> Upload.
    """
    try:
        bot = App(channel_profile=channel)
        bot.run(dry_run=dry)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
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
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise typer.Exit(code=1)

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

    config["channels"][channel] = {
        "secrets_file": secrets_file,
        "token_file": token_file,
        "youtube_channel_name": youtube_channel_name,
        "playlist_id": playlist_id,
        "tags": tags,
        "title_templates": title_templates,
        "description_template": description_template
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, sort_keys=False, allow_unicode=True)
    
    logger.info(f"Successfully added channel '{channel}' to {config_path}")


if __name__ == "__main__":
    app()
