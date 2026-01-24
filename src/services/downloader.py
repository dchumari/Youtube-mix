import yt_dlp
import time
from pathlib import Path
from typing import Optional
from ..utils.logger import logger

class YtLogger:
    def debug(self, msg):
        # Filter out too much noise if needed, or keep it for debugging
        if output_is_error(msg):
             logger.debug(f"[yt-dlp] {msg}")
        pass 

    def warning(self, msg):
        logger.warning(f"[yt-dlp] {msg}")

    def error(self, msg):
        logger.error(f"[yt-dlp] {msg}")

def output_is_error(msg):
    return "error" in msg.lower() or "warning" in msg.lower()

class Downloader:
    def __init__(self, download_folder: str = "downloads"):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

    def download_audio(self, url: str, subfolder: str = None) -> Optional[Path]:
        """Downloads audio from YouTube URL."""
        target_folder = self.download_folder / subfolder if subfolder else self.download_folder
        target_folder.mkdir(parents=True, exist_ok=True)
        
        

        ydl_opts = {
            "outtmpl": f"{target_folder}/%(title)s.%(ext)s",
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "logger": YtLogger(),
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "web", "mweb"],  # Use ios client first
                    "skip": ["dash", "hls"],  # Skip problematic formats
                }
            },
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cachedir": False,
            "extractor_retries": 5,
            "retries": 5,
            "retry_sleep_functions": {"extractor": lambda x: 5},
            "sleep_interval_requests": 2,
            "sleep_interval": 2,
            "max_sleep_interval": 10,
            "compat_opts": ["no-live-chat"],
            "check_formats": "selected",
            "hls_prefer_native": False,  # Use external downloader for HLS
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        }

        return self._download(url, ydl_opts, "audio")

    def download_video(self, url: str, subfolder: str = None) -> Optional[Path]:
        """Downloads video from YouTube URL."""
        target_folder = self.download_folder / subfolder if subfolder else self.download_folder
        target_folder.mkdir(parents=True, exist_ok=True)

        

        ydl_opts = {
            "outtmpl": f"{target_folder}/%(title)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": False,
            "verbose": True,
            "no_warnings": False,
            "logger": YtLogger(),
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "web", "mweb"],  # Use ios client first
                    "skip": ["dash", "hls"],  # Skip problematic formats
                }
            },
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cachedir": False,
            "extractor_retries": 5,
            "retries": 5,
            "retry_sleep_functions": {"extractor": lambda x: 5},
            "sleep_interval_requests": 2,
            "sleep_interval": 2,
            "max_sleep_interval": 10,
            "compat_opts": ["no-live-chat"],
            "check_formats": "selected",
            "hls_prefer_native": False,  # Use external downloader for HLS
        }

        return self._download(url, ydl_opts, "video")

    def _download(self, url: str, opts: dict, type_label: str) -> Optional[Path]:
        # Use the retry count from the options or default
        max_retries = opts.get("extractor_retries", opts.get("retries", 3))
        
        # Track state across retries
        
        # Clients to cycle through.
        # 'ios': Often less bot detection, good fallback.
        # 'tv': Good for bypassing some restricts.
        # 'web': Basic fallback.
        # 'android': Standard mobile.
        clients = ["ios", "tv", "web", "android"]
        client_index = 0

        for attempt in range(max_retries):
            current_opts = opts.copy()
            
            # Select client for this attempt
            current_client = clients[client_index % len(clients)]
            
            # Rotate client on next attempt
            client_index += 1
            
            # Update extractor args with the chosen client
            if "extractor_args" not in current_opts:
                current_opts["extractor_args"] = {}
            if "youtube" not in current_opts["extractor_args"]:
                current_opts["extractor_args"]["youtube"] = {}
            
            # Force the client using arguments
            # Note: mweb/web usually good for public, android/ios for signed.
            current_opts["extractor_args"]["youtube"]["player_client"] = [current_client]
            
            logger.info(f"Attempt {attempt + 1}/{max_retries} using client '{current_client}'...")

            try:
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    # First, check if the video has downloadable formats
                    info = ydl.extract_info(url, download=False)

                    # Check for available formats (ignoring storyboards)
                    has_downloadable_format = False
                    if 'formats' in info and info['formats']:
                        for fmt in info['formats']:
                            vcodec = fmt.get('vcodec', 'none')
                            acodec = fmt.get('acodec', 'none')
                            format_note = fmt.get('format_note', '').lower()
                            if (vcodec != 'none' or acodec != 'none') and 'storyboard' not in format_note:
                                has_downloadable_format = True
                                break

                    if not has_downloadable_format:
                        # If no formats and we are using mweb/android, it might be a bot block.
                        # Raising DownloadError triggers the catch block where we retry/rotate.
                        raise yt_dlp.DownloadError(f"No downloadable formats found with client {current_client}")

                    # Download
                    info = ydl.extract_info(url, download=True)
                    if 'entries' in info:
                        info = info['entries'][0]

                    filename = ydl.prepare_filename(info)
                    final_path = Path(filename)
                    if type_label == "audio":
                        final_path = Path(filename).with_suffix(".mp3")

                    if not final_path.exists() or final_path.stat().st_size == 0:
                        raise Exception("The downloaded file is empty")

                    logger.info(f"Downloaded {type_label}: {final_path.name}")
                    return final_path

            except (yt_dlp.DownloadError, Exception) as e:
                error_msg = str(e).lower()
                logger.warning(f"Download attempt {attempt + 1} failed with client {current_client}: {e}")

                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {url} after {max_retries} attempts.")
                    return None

                sleep_time = 5
                logger.info(f"Waiting {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
        return None
