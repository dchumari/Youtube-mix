from pathlib import Path
import yaml
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from src.app import App
from src.utils.logger import logger

console = Console()

class InteractiveMenu:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        path = Path(self.config_path)
        if not path.exists():
            console.print(f"[red]Config file not found: {self.config_path}[/red]")
            return {"channels": {}}
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def display_welcome(self):
        title = Text("YouTube Music Mix Automation", style="bold magenta")
        subtitle = Text("Interactive CLI Mode", style="italic cyan")
        panel = Panel(
            Text.assemble(title, "\n", subtitle),
            border_style="blue",
            expand=False
        )
        console.print(panel)

    def run(self):
        self.display_welcome()
        
        while True:
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "Run Workflow",
                    "Authenticate Channel",
                    "Tools (Twixtor/Utils)",
                    "Manage Channels",
                    "Exit"
                ]
            ).ask()

            if action == "Exit":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif action == "Run Workflow":
                self.run_workflow_menu()
            elif action == "Authenticate Channel":
                self.auth_menu()
            elif action == "Tools (Twixtor/Utils)":
                self.tools_menu()
            elif action == "Manage Channels":
                self.manage_channels_menu()

    def _get_channels(self):
        channels = list(self.config.get("channels", {}).keys())
        if not channels:
            console.print("[red]No channels found in settings.yaml[/red]")
            return []
        return channels

    def run_workflow_menu(self):
        channels = self._get_channels()
        if not channels: return

        channel = questionary.select(
            "Select a channel profile:",
            choices=channels + ["Back"]
        ).ask()

        if channel == "Back": return

        # Load defaults from profile
        profile = self.config["channels"][channel]
        defaults = self.config.get("defaults", {})
        
        default_mix_min = profile.get("mix_minutes") or defaults.get("mix_minutes", 3)
        default_track_limit = profile.get("track_limit") or defaults.get("track_limit", 10)
        default_cat = profile.get("video_category") or defaults.get("video_category", 2)
        default_clips = profile.get("video_clips") or defaults.get("video_clips", 5)
        default_posting = profile.get("posting") or defaults.get("posting", "private")
        default_res = profile.get("resolution") or defaults.get("resolution", "1080")

        # Interactive configuration
        customize = questionary.confirm("Customize settings for this run?", default=False).ask()
        
        settings = {
            "mix_minutes": default_mix_min,
            "track_limit": default_track_limit,
            "video_category": default_cat,
            "video_clips": default_clips,
            "posting": default_posting,
            "resolution": default_res,
            "video_folders": None
        }

        if customize:
            settings["mix_minutes"] = int(questionary.text("Mix Duration (minutes):", default=str(default_mix_min)).ask())
            settings["track_limit"] = int(questionary.text("Track Limit:", default=str(default_track_limit)).ask())
            settings["video_category"] = int(questionary.text("Video Categories (Twixtor):", default=str(default_cat)).ask())
            settings["video_clips"] = int(questionary.text("Clips per Category:", default=str(default_clips)).ask())
            settings["posting"] = questionary.select("Privacy Status:", choices=["private", "public", "unlisted"], default=default_posting).ask()
            settings["resolution"] = questionary.select("Resolution:", choices=["720", "1080", "2k", "4k"], default=str(default_res)).ask()
            
            use_custom_folders = questionary.confirm("Provide custom Video Drive Folders?", default=False).ask()
            if use_custom_folders:
                 settings["video_folders"] = questionary.text("Google Drive Folder Link(s):").ask()

        dry_run = questionary.confirm("Dry Run (Skip Upload)?", default=False).ask()

        confirm_msg = f"""
[bold green]Ready to start![/bold green]
Channel: [cyan]{channel}[/cyan]
Settings:
  - Mix Minutes: {settings['mix_minutes']}
  - Track Limit: {settings['track_limit']}
  - Resolution: {settings['resolution']}
  - Posting: {settings['posting']}
  - Dry Run: {dry_run}
"""
        console.print(Panel(confirm_msg.strip(), title="Summary"))
        
        if questionary.confirm("Proceed?", default=True).ask():
            try:
                bot = App(
                    channel_profile=channel,
                    mix_minutes=settings["mix_minutes"],
                    track_limit=settings["track_limit"],
                    video_category=settings["video_category"],
                    video_clips=settings["video_clips"],
                    posting=settings["posting"],
                    video_folders=settings["video_folders"],
                    resolution=settings["resolution"]
                )
                bot.run(dry_run=dry_run)
                console.print("\n[bold green]Workflow Completed Successfully![/bold green]\n")
            except Exception as e:
                console.print(f"\n[bold red]Error Occurred:[/bold red] {e}\n")
                logger.error(f"Menu workflow error: {e}")

    def auth_menu(self):
        channels = self._get_channels()
        if not channels: return

        channel = questionary.select(
            "Select a channel to authenticate:",
            choices=channels + ["Back"]
        ).ask()

        if channel == "Back": return

        try:
            bot = App(channel_profile=channel)
            console.print(f"[yellow]Launching browser for {channel} authentication...[/yellow]")
            bot.auth_only()
             # Check for refresh token logic similar to main.py
            if bot.uploader.token_file.exists():
                import json
                with open(bot.uploader.token_file, "r") as f:
                    token_data = json.load(f)
                    refresh = token_data.get("refresh_token")
                    if refresh:
                         console.print(f"[green]Refresh Token Found:[/green] {refresh}")
                         # We could update config here too if we import the utility or duplicate logic
                         # For now, just notifying is good as main.py logic handles it usually
        except Exception as e:
            console.print(f"[red]Auth Failed:[/red] {e}")

    def tools_menu(self):
        tool = questionary.select(
            "Select a tool:",
            choices=[
                "Get Twixtor Links",
                "Back"
            ]
        ).ask()

        if tool == "Get Twixtor Links":
            self.twixtor_tool()

    def twixtor_tool(self):
        num_series = int(questionary.text("Number of Series:", default="5").ask())
        num_clips = int(questionary.text("Number of Clips:", default="5").ask())
        
        try:
            # Just use primary profile for generic tool usage if needed, or ask
            bot = App(channel_profile="primary") 
            links = bot.get_twixtor_links(num_series, num_clips)
            if links:
                console.print(Panel("\n".join(links), title="Twixtor Links"))
            else:
                console.print("[yellow]No links found.[/yellow]")
        except Exception as e:
             console.print(f"[red]Error:[/red] {e}")

    def manage_channels_menu(self):
        console.print("[italic]Channel management is best done via settings.yaml directly for now, or use 'delete_channel' from CLI.[/italic]")
        # Placeholder for future expansion
        questionary.press_any_key_to_continue().ask()
