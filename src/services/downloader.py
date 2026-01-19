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
        
        cookie_file = Path("config/cookies.txt")

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
                    "player_client": ["android", "ios"],  # Use mobile clients to avoid signature issues
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

        if cookie_file.exists():
            ydl_opts["cookiefile"] = str(cookie_file)
            logger.info("Using cookies for YouTube audio download.")

        return self._download(url, ydl_opts, "audio")

    def download_video(self, url: str, subfolder: str = None) -> Optional[Path]:
        """Downloads video from YouTube URL."""
        target_folder = self.download_folder / subfolder if subfolder else self.download_folder
        target_folder.mkdir(parents=True, exist_ok=True)

        cookie_file = Path("config/cookies.txt")

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
                    "player_client": ["android", "ios"],  # Use mobile clients to avoid signature issues
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

        if cookie_file.exists():
            ydl_opts["cookiefile"] = str(cookie_file)
            logger.info("Using cookies for YouTube video download.")
        
        return self._download(url, ydl_opts, "video")

    def _download(self, url: str, opts: dict, type_label: str) -> Optional[Path]:
        # Use the retry count from the options or default to 3
        max_retries = opts.get("extractor_retries", opts.get("retries", 3))

        for attempt in range(max_retries):
            current_opts = opts.copy()

            # Adjust extractor args based on the attempt number for signature/challenge solving
            # Adjust extractor args based on the attempt number for signature/challenge solving
            # if attempt == 1:
            #     if "extractor_args" in current_opts:
            #         if "youtube" in current_opts["extractor_args"]:
            #             current_opts["extractor_args"]["youtube"]["player_client"] = ["web"]
            # elif attempt == 2:
            #     if "extractor_args" in current_opts:
            #         if "youtube" in current_opts["extractor_args"]:
            #             current_opts["extractor_args"]["youtube"]["player_client"] = ["android", "ios"]
            # elif attempt > 2:
            #     if "extractor_args" in current_opts:
            #         if "youtube" in current_opts["extractor_args"]:
            #             current_opts["extractor_args"]["youtube"]["player_client"] = ["tv_embedded", "web"]

            try:
                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    # First, check if the video has downloadable formats by getting available formats
                    info = ydl.extract_info(url, download=False)

                    # Check if the video has downloadable formats
                    has_downloadable_format = False
                    if 'formats' in info and info['formats']:
                        for fmt in info['formats']:
                            # Look for formats that have actual video/audio content (not just storyboards)
                            vcodec = fmt.get('vcodec', 'none')
                            acodec = fmt.get('acodec', 'none')
                            format_note = fmt.get('format_note', '').lower()

                            if (vcodec != 'none' or acodec != 'none') and 'storyboard' not in format_note:
                                has_downloadable_format = True
                                break

                    # If no downloadable formats found, skip this video
                    if not has_downloadable_format:
                        logger.warning(f"No downloadable formats available for {url}. Skipping...")
                        return None

                    # Now download the actual content
                    info = ydl.extract_info(url, download=True)

                    # Handle ytsearch results which return a list of entries
                    if 'entries' in info:
                        info = info['entries'][0]

                    filename = ydl.prepare_filename(info)

                    # Check if the file is empty after download
                    final_path = Path(filename)
                    if type_label == "audio":
                        # FFmpegExtractAudio postprocessor changes extension to mp3
                        final_path = Path(filename).with_suffix(".mp3")

                    # Verify that the file exists and is not empty
                    if not final_path.exists() or final_path.stat().st_size == 0:
                        raise Exception("The downloaded file is empty")

                    logger.info(f"Downloaded {type_label}: {final_path.name}")
                    return final_path

            except yt_dlp.DownloadError as e:
                error_msg = str(e).lower()
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed for {url}: {e}")

                # Check if this is a signature/challenge solving error
                if any(keyword in error_msg for keyword in ["signature", "challenge", "javascript", "empty"]):
                    logger.warning(f"Possible signature/challenge solving issue detected for {url}.")

                # Check if it's a format availability error
                if "requested format is not available" in str(e).lower() or "only images are available" in str(e).lower():
                    logger.warning(f"No downloadable formats available for {url}. Skipping...")
                    if "only images are available" in str(e).lower():
                        return None  # Skip this video if only images are available

                # If format error, try to list formats for debugging in logs
                if "requested format is not available" in str(e).lower() and attempt == 0:
                    logger.info(f"Attempting to list available formats for troubleshooting {url}...")
                    try:
                        debug_opts = current_opts.copy()
                        debug_opts.update({"listformats": True, "quiet": False})
                        with yt_dlp.YoutubeDL(debug_opts) as debug_ydl:
                            debug_ydl.extract_info(url, download=False)
                    except Exception:
                        pass

                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {url} after {max_retries} attempts.")
                    return None

                # Use a more progressive backoff strategy
                sleep_time = min(10 * (attempt + 1), 30)  # Increase sleep time with each attempt, max 30 seconds
                logger.info(f"Waiting {sleep_time} seconds before next attempt...")
                time.sleep(sleep_time)
        return None
