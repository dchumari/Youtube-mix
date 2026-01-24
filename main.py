import typer
from pathlib import Path
from src.app import App
from src.utils.logger import logger

app = typer.Typer(help="YouTube Music Mix Automation Tool")

@app.command()
def run(
    channel: str = typer.Option("primary", help="Channel profile to use (defined in settings.yaml)"),
    dry: bool = typer.Option(False, "--dry", help="Skip upload step"),
    source: str = typer.Option(None, "--source", help="Video source: twixtor, drive, local"),
    path: str = typer.Option(None, "--path", help="Path (local) or URL (drive/web) override")
):
    """
    Runs the full automation workflow: Fetch -> Download -> Mix -> Upload.
    """
    try:
        bot = App(channel_profile=channel)
        bot.run(dry_run=dry, video_source=source, video_path=path)
    except ValueError as e:
        if f"Profile '{channel}' not found" in str(e):
             logger.error(f"Channel '{channel}' not found in settings.yaml. Run 'python main.py auth --channel {channel}' to create it.")
             raise typer.Exit(code=1)
        else:
             logger.error(f"Fatal error: {e}")
             raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise typer.Exit(code=1)

def add_channel_interactive(name: str):
    """Interactive prompts to add a new channel configuration."""
    typer.echo(f"\n🆕 Configuring new channel: {name}")
    typer.echo("-----------------------------------")
    
    # Pre-check for duplicate key to avoid corruption
    settings_path = "config/settings.yaml"
    if Path(settings_path).exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple check for the key at the start of a line with indentation or no indentation
            # But since it's top level under 'channels' usually, or root?
            # settings.yaml structure is:
            # channels:
            #   primary:
            # We are appending. If we append, we assume it's under 'channels' if we just append?
            # Wait, the current append implementation DOES NOT indent correctly if it assumes top level.
            # actually looking at previous code: f.write(f"\n  {name}:\n") -> 2 spaces indent.
            # This implies it's being added to 'channels' block?
            # BUT 'channels:' key is at the top. If we append to the END of the file,
            # and the previous line was indented, it MIGHT be okay, OR it might be treated as top level if previous block ended?
            # Actually, YAML indentation is context sensitive.
            # If the last line of the file is part of 'channels', appending with 2 spaces continues 'channels'.
            # If the last line was root level (e.g. 'defaults:'), then 2 spaces might be wrong or right depending on structure.
            # In existing settings.yaml, 'channels:' is defined. All channels are indented 2 spaces.
            # So appending "\n  {name}:" works IF the file ends while still effectively "inside" channels (or just indent matches).
            
            # Robust duplicates check:
            if f"\n  {name}:" in content or f"\n{name}:" in content:
                 typer.echo(f"⚠️  Channel '{name}' already seems to exist in {settings_path}. Aborting to prevent corruption.")
                 return

    # Defaults
    default_secrets = "config/client_secrets.json"
    default_token = f"config/tokens/{name}_token.json"
    
    secrets = typer.prompt("Secrets file path", default=default_secrets)
    token = typer.prompt("Token file path", default=default_token)
    playlist_id = typer.prompt("Spotify Playlist ID")
    yt_name = typer.prompt("YouTube Channel Name")
    tags_input = typer.prompt("Tags (comma separated)", default="music, mix")
    
    # Prepare YAML block
    # Quote tags to ensure valid YAML flow sequence
    tags_list_str = ', '.join(f'"{t.strip()}"' for t in tags_input.split(','))
    tags_yaml = f"[{tags_list_str}]"
    
    try:
        with open(settings_path, "a", encoding="utf-8") as f:
            f.write(f"\n  \"{name}\":\n")
            f.write(f"    secrets_file: \"{secrets}\"\n")
            f.write(f"    token_file: \"{token}\"\n")
            f.write(f"    tags: {tags_yaml}\n")
            f.write(f"    playlist_id: \"{playlist_id}\"\n")
            f.write(f"    youtube_channel_name: \"{yt_name}\"\n")
            # Defaults to ensure functionality
            f.write(f"    video_provider: \"twixtor\"\n") 
            f.write(f"    title_templates:\n")
            f.write(f"      - \"New Mix 2025 - {name} 🎵\"\n")
            f.write(f"    description_template: |\n")
            f.write(f"      New Mix from {name}!\n\n")
            f.write(f"      {{time_stamps}}\n")
            
        typer.echo(f"✅ Channel '{name}' added to {settings_path}\n")
        
    except Exception as e:
        logger.error(f"Failed to write to settings.yaml: {e}")
        raise typer.Exit(code=1)

@app.command()
def auth(
    channel: str = typer.Option("primary", help="Channel profile to authenticate")
):
    """
    Runs the authentication flow for a specific channel.
    If the channel doesn't exist, asks to create it.
    """
    try:
        bot = App(channel_profile=channel)
        bot.auth_only()
    except ValueError as e:
        # Check if it's the specific "Profile not found" error
        if f"Profile '{channel}' not found" in str(e):
            if typer.confirm(f"Channel '{channel}' not found in settings. Do you want to add it now?"):
                add_channel_interactive(channel)
                # Retry
                try:
                    bot = App(channel_profile=channel)
                    bot.auth_only()
                except Exception as retry_e:
                    logger.error(f"Auth failed after creation: {retry_e}")
                    raise typer.Exit(code=1)
            else:
                typer.echo("Aborted.")
                raise typer.Exit(code=0)
        else:
            logger.error(f"Configuration error: {e}")
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
