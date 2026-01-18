import yaml
import shutil
import random
import time
from pathlib import Path
from .services.music_provider import SpotifyProvider, YouTubeMusicProvider
from .services.downloader import Downloader
from .services.mixer import Mixer
from .services.uploader import YoutubeUploader
from .services.twixtor import TwixtorProvider
from .services.drive_provider import DriveProvider
from .utils.logger import logger

class App:
    def __init__(self, channel_profile: str = "primary", config_path: str = "config/settings.yaml"):
        self.channel_profile = channel_profile
        self.config = self._load_config(config_path)
        
        self.profile = self.config["channels"].get(channel_profile)
        if not self.profile:
            raise ValueError(f"Profile '{channel_profile}' not found in settings.")
            
        self.defaults = self.config.get("defaults", {})
        
        # Initialize Services
        self.music_provider = SpotifyProvider()
        self.ytm_provider = YouTubeMusicProvider()
        self.downloader = Downloader(self.defaults.get("download_folder", "downloads"))
        self.mixer = Mixer()
        self.twixtor = TwixtorProvider(Path(self.defaults.get("download_folder", "downloads")) / "visuals")
        self.drive_provider = DriveProvider(Path(self.defaults.get("download_folder", "downloads")) / "visuals_drive")
        self.uploader = YoutubeUploader(
            secrets_file=self.profile["secrets_file"],
            token_file=self.profile["token_file"]
        )

    def _load_config(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run(self, dry_run: bool = False, video_source: str = None, video_path: str = None):
        logger.info(f"Starting workflow for channel: {self.channel_profile}")
        
        try:
            # 0. Initial Cleanup (ensure fresh start)
            self.cleanup()
            
            # Ensure visuals directory exists (fix WinError 3 after cleanup)
            self.twixtor.download_folder.mkdir(parents=True, exist_ok=True)

            # 1. Get Tracks
            playlist_id = self.profile.get("playlist_id")
            logger.info("Fetching tracks from Spotify...")
            tracks = self.music_provider.get_tracks(
                playlist_id, 
                limit=self.defaults.get("track_limit", 50)
            )
            
            # Calculate needed duration
            target_minutes = self.defaults.get("mix_minutes", 60)
            selected_tracks = []
            current_duration_ms = 0
            target_duration_ms = target_minutes * 60 * 1000
            
            for track in tracks:
                if current_duration_ms >= target_duration_ms:
                    break
                selected_tracks.append(track)
                current_duration_ms += track["duration_ms"]
                
            logger.info(f"Selected {len(selected_tracks)} tracks for ~{target_minutes} minutes.")

            # 2. Download Audio
            audio_paths = []
            playlist_folder_name = f"{self.channel_profile}_mix_source"
            
            logger.info("Searching and downloading official audio tracks...")
            for track in selected_tracks:
                # Use YTMusic to find official audio
                video_url = self.ytm_provider.find_track_url(track['name'], track['artist'])
                
                if not video_url:
                    # Fallback to generic search if YTMusic fails
                    video_url = f"ytsearch1:{track['name']} {track['artist']} lyrics"
                
                path = self.downloader.download_audio(video_url, subfolder=playlist_folder_name)
                if path:
                    audio_paths.append(path)
                
                # Sleep between downloads to avoid being flagged
                time.sleep(random.uniform(3, 7))
                    
            if not audio_paths:
                logger.error("No audio tracks downloaded.")
                return

            # 3. Get Visuals
            logger.info("Getting visuals...")
            
            # Determine Source: CLI > Config > Default
            source = video_source or self.profile.get("video_provider", "web")
            # Legacy mapping: "web" -> "twixtor" if not specified otherwise
            if source == "web" and "twixtor_url" not in self.profile:
                source = "twixtor"
            
            # Determine Path/URL
            path_or_url = video_path
            
            video_paths = []
            
            if source == "local":
                target_path = Path(path_or_url) if path_or_url else Path(self.profile.get("local_video_path", ""))
                logger.info(f"Using local videos from: {target_path}")
                
                if not target_path.exists() or not target_path.is_dir():
                    logger.error(f"Local video path does not exist: {target_path}")
                    return

                # Glob videos
                for ext in ["*.mp4", "*.mkv", "*.mov", "*.avi", "*.webm"]:
                    video_paths.extend(list(target_path.glob(ext)))
                    
            elif source == "drive":
                target_url = path_or_url or self.profile.get("drive_url")
                if not target_url:
                     logger.error("Drive URL not provided for drive source.")
                     return
                
                video_paths = self.drive_provider.download_videos(target_url)
                
            else: # Default/Twixtor
                # If path_or_url is provided, can TwixtorProvider use it?
                # Currently TwixtorProvider is hardcoded to animeworldtwixtor, but we could add override.
                # implementing basic call for now.
                video_paths = self.twixtor.get_clips(
                    num_series=self.defaults.get("video_category", 5), 
                    num_clips=self.defaults.get("video_clips", 5)
                )
            
            if not video_paths:
                 logger.error(f"No visuals found from source: {source}")
                 return

            # 4. Mix
            logger.info("Creating Mix...")
            mix_folder = Path(self.defaults.get("download_folder", "downloads")) / "output"
            output_file = mix_folder / f"final_mix_{self.channel_profile}.mp4"
            
            timestamps, mix_file = self.mixer.create_mix(audio_paths, video_paths, output_file)
            
            logger.info(f"Mix created at: {mix_file}")
            
            if dry_run:
                logger.info("Dry run complete. Skipping upload.")
                return

            # 5. Upload
            logger.info("Uploading to YouTube...")
            
            # Description formatting using template
            time_stamps_str = "\n".join(timestamps)
            desc_template = self.profile.get("description_template", "Enjoy this mix!\n\n{time_stamps}")
            desc = desc_template.replace("{time_stamps}", time_stamps_str)
            
            # Title selection
            title_templates = self.profile.get("title_templates", [])
            if title_templates:
                video_title = random.choice(title_templates)
            else:
                video_title = f"Best Music Mix 2025 - {self.channel_profile.title()} 🎵"

            video_id = self.uploader.upload_video(
                file_path=mix_file,
                title=video_title,
                description=desc,
                tags=self.profile.get("tags", []),
                privacy_status="public" 
            )
            
            logger.info(f"Workflow finished successfully! Video: https://youtu.be/{video_id}")

        except (Exception, KeyboardInterrupt) as e:
            logger.error(f"Process interrupted or failed: {e}")
            self.cleanup()
            raise

    def cleanup(self):
        """Removes all downloaded files to ensure a fresh state."""
        logger.info("Cleaning up download directories...")
        download_folder = Path(self.defaults.get("download_folder", "downloads"))
        if download_folder.exists():
            try:
                # We use shutil.rmtree and re-create to be thorough
                # But we might want to keep the 'output' folder if it contains the final product?
                # User said "removes all downloaded files". 
                # Usually that means the source files.
                # If it failed, we definitely want everything gone.
                shutil.rmtree(download_folder)
                download_folder.mkdir(parents=True, exist_ok=True)
                logger.info("Cleanup successful.")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

    def auth_only(self):
        """Runs authentication flow only"""
        logger.info("Running Authentication Flow...")
        self.uploader.authenticate(headless=False)
