import typer
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
        bot = App(channel_profile=channel)
        bot.auth_only()
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
