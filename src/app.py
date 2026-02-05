import yaml
import shutil
import random
from pathlib import Path
from typing import List, Optional
from .services.music_provider import SpotifyProvider, YouTubeMusicProvider
from .services.downloader import Downloader
from .services.mixer import Mixer
from .services.uploader import YoutubeUploader
from .services.twixtor import TwixtorProvider
import gdown
from .utils.logger import logger

class App:
    def __init__(
        self, 
        channel_profile: str = "primary", 
        config_path: str = "config/settings.yaml",
        mix_minutes: int = None,
        track_limit: int = None,
        video_category: int = None,
        video_clips: int = None,
        posting: str = None,
        video_folders: str = None
    ):
        self.channel_profile = channel_profile
        self.config = self._load_config(config_path)
        
        self.profile = self.config["channels"].get(channel_profile)
        if not self.profile:
            raise ValueError(f"Profile '{channel_profile}' not found in settings.")
            
        self.defaults = self.config.get("defaults", {})
        
        # Override settings (CLI > Channel > Defaults)
        self.mix_minutes = mix_minutes or self.profile.get("mix_minutes") or self.defaults.get("mix_minutes", 3)
        self.track_limit = track_limit or self.profile.get("track_limit") or self.defaults.get("track_limit", 10)
        self.video_category = video_category or self.profile.get("video_category") or self.defaults.get("video_category", 2)
        self.video_clips = video_clips or self.profile.get("video_clips") or self.defaults.get("video_clips", 5)
        self.posting = posting or self.profile.get("posting") or self.defaults.get("posting", "private")
        self.video_folders = video_folders or self.profile.get("video_folders")

        # Initialize Services
        self.music_provider = SpotifyProvider()
        self.ytm_provider = YouTubeMusicProvider()
        self.downloader = Downloader(self.defaults.get("download_folder", "downloads"))
        self.mixer = Mixer()
        self.twixtor = TwixtorProvider(Path(self.defaults.get("download_folder", "downloads")) / "visuals")
        self.uploader = YoutubeUploader(self.profile)

    def _load_config(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run(self, dry_run: bool = False):
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
                limit=self.track_limit
            )
            
            # Calculate needed duration
            target_minutes = self.mix_minutes
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
                    
            if not audio_paths:
                logger.error("No audio tracks downloaded.")
                return

            # 3. Get Visuals (Twixtors)
            logger.info("Fetching visuals...")
            folder_url = self.video_folders
            
            if folder_url:
                logger.info(f"Using Google Drive folder for visuals: {folder_url}")
                video_paths = self._get_visuals_from_drive(folder_url)
            else:
                logger.info("Scraping and downloading Twixtor visuals from web...")
                video_paths = self.twixtor.get_clips(
                    num_series=self.video_category, 
                    num_clips=self.video_clips
                )
            
            if not video_paths:
                 logger.error("No visuals found/downloaded.")
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

            # 5. Get Thumbnail
            thumbnail_path = None
            thumb_folder_url = self.profile.get("thumbnail_folders")
            if thumb_folder_url:
                logger.info(f"Fetching random thumbnail from: {thumb_folder_url}")
                thumbnail_path = self._get_thumbnail_from_drive(thumb_folder_url)

            # 6. Upload
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
                privacy_status=self.posting,
                thumbnail_path=thumbnail_path
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

    def get_twixtor_links(self, num_series: int = 5, num_clips: int = 5) -> List[str]:
        """Scrapes and returns Twixtor Drive links"""
        return self.twixtor.scrape_drive_links(num_series, num_clips)

    def _get_visuals_from_drive(self, folder_url_input) -> List[Path]:
        """
        Downloads selected videos from one or more Google Drive folders.
        Supports single string URL or list of string URLs.
        """
        import re
        
        # Normalize input to a list
        if isinstance(folder_url_input, str):
            folder_urls = [folder_url_input]
        elif isinstance(folder_url_input, list):
            folder_urls = folder_url_input
        else:
            logger.error(f"Invalid format for video_folders: {type(folder_url_input)}")
            return []

        all_video_files = []
        download_folder = self.twixtor.download_folder
        download_folder.mkdir(parents=True, exist_ok=True)

        for url in folder_urls:
            folder_id = None
            match = re.search(r'folders/([a-zA-Z0-9_-]+)', url)
            if match:
                folder_id = match.group(1)
                clean_url = f"https://drive.google.com/drive/folders/{folder_id}"
            else:
                clean_url = url

            logger.info(f"Listing videos via gdown from: {clean_url}")
            
            try:
                # 1. Get the list of files without downloading
                files = gdown.download_folder(url=clean_url, skip_download=True, quiet=True)
                
                if not files:
                    logger.warning(f"gdown failed to retrieve file list for: {clean_url}")
                    continue
                
                # 2. Filter for video files
                video_files = [f for f in files if f.path.lower().endswith(('.mp4', '.mkv', '.mov', '.avi'))]
                
                if not video_files:
                    logger.warning(f"No video files found in folder: {clean_url}")
                    continue
                
                all_video_files.extend(video_files)
                logger.info(f"Found {len(video_files)} videos in {clean_url}")

            except Exception as e:
                logger.error(f"Failed to list folder {clean_url}: {e}")

        if not all_video_files:
            logger.error("No video files found across all provided Drive folders.")
            return []

        # 3. Shuffle and select a subset
        num_clips = self.video_clips
        random.shuffle(all_video_files)
        selected_files = all_video_files[:num_clips]
        
        logger.info(f"Selected {len(selected_files)} total videos from aggregated folders.")
        
        # 4. Download each selected file
        downloaded_paths = []
        for i, f in enumerate(selected_files):
            file_id = f.id
            file_name = f.path or f'clip_{i+1}.mp4'
            target_path = download_folder / file_name
            
            # Avoid downloading the same file multiple times if it appears in different folders
            # (though unlikely with unique IDs, but good practice)
            if target_path.exists():
                logger.info(f"File already exists, skipping download: {file_name}")
                downloaded_paths.append(target_path)
                continue

            logger.info(f"Downloading [{i+1}/{len(selected_files)}]: {file_name}")
            try:
                downloaded_path = gdown.download(id=file_id, output=str(target_path), quiet=True, fuzzy=True)
                if downloaded_path:
                    downloaded_paths.append(Path(downloaded_path))
            except Exception as e:
                logger.warning(f"Failed to download video {file_name} (ID: {file_id}): {e}")
                # Continue to next file
                continue
            
        return downloaded_paths
    def _get_thumbnail_from_drive(self, folder_url: str) -> Optional[Path]:
        """Downloads ONE random image from a Google Drive folder using gdown."""
        import re
        folder_id = None
        match = re.search(r'folders/([a-zA-Z0-9_-]+)', folder_url)
        if match:
            folder_id = match.group(1)
            clean_url = f"https://drive.google.com/drive/folders/{folder_id}"
        else:
            clean_url = folder_url

        try:
            # Create a separate folder for thumbnails
            thumb_dir = Path(self.defaults.get("download_folder", "downloads")) / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)

            # 1. Get the list of files without downloading
            files = gdown.download_folder(url=clean_url, skip_download=True, quiet=True)
            
            if not files:
                logger.error("gdown failed to retrieve thumbnail file list.")
                return None
            
            # 2. Filter for image files
            image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
            image_files = [f for f in files if f.path.lower().endswith(image_extensions)]
            
            if not image_files:
                logger.warning("No image files found in the Thumbnail Drive folder.")
                return None
            
            logger.info(f"Found {len(image_files)} thumbnails in Drive folder.")
            
            # 3. Select ONE random image
            selected_file = random.choice(image_files)
            
            file_id = selected_file.id
            file_name = selected_file.path or 'thumbnail.jpg'
            target_path = thumb_dir / file_name
            
            logger.info(f"Downloading random thumbnail: {file_name}")
            try:
                downloaded_path = gdown.download(id=file_id, output=str(target_path), quiet=True, fuzzy=True)
                if downloaded_path:
                    return Path(downloaded_path)
            except Exception as e:
                logger.error(f"Failed to download random thumbnail {file_name}: {e}")
                return None
            
            return None

        except Exception as e:
            logger.error(f"Thumbnail Drive download failed: {e}")
            return None
