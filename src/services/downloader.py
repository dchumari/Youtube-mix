import yt_dlp
import time
from pathlib import Path
from typing import Optional
from ..utils.logger import logger

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
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cachedir": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "web"],
                }
            },
        }

        cookie_file = Path("config/cookies.txt")
        if cookie_file.exists():
            ydl_opts["cookiefile"] = str(cookie_file)
            logger.info("Using cookies for YouTube audio download.")

        return self._download(url, ydl_opts, "audio")

    def download_video(self, url: str, subfolder: str = None) -> Optional[Path]:
        """Downloads video from YouTube URL."""
        target_folder = self.download_folder / subfolder if subfolder else self.download_folder
        target_folder.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            "outtmpl": f"{target_folder}/%(title)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cachedir": False,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "web"],
                }
            },
        }
        
        cookie_file = Path("config/cookies.txt")
        if cookie_file.exists():
            ydl_opts["cookiefile"] = str(cookie_file)
            logger.info("Using cookies for YouTube video download.")
        
        return self._download(url, ydl_opts, "video")

    def _download(self, url: str, opts: dict, type_label: str) -> Optional[Path]:
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    # Handle ytsearch results which return a list of entries
                    if 'entries' in info:
                        info = info['entries'][0]

                    filename = ydl.prepare_filename(info)
                    
                    if type_label == "audio":
                        # FFmpegExtractAudio postprocessor changes extension to mp3
                        final_path = Path(filename).with_suffix(".mp3")
                    else:
                        final_path = Path(filename)
                        
                    logger.info(f"Downloaded {type_label}: {final_path.name}")
                    return final_path
                    
            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
                
                # If format error, try to list formats for debugging in logs
                if "Requested format is not available" in str(e) and attempt == 0:
                    logger.info(f"Attempting to list available formats for troubleshooting {url}...")
                    try:
                        debug_opts = opts.copy()
                        debug_opts.update({"listformats": True, "quiet": False})
                        with yt_dlp.YoutubeDL(debug_opts) as ydl:
                            ydl.extract_info(url, download=False)
                    except Exception:
                        pass

                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {url} after {max_retries} attempts.")
                    return None
                time.sleep(10)  # Wait longer between retries to avoid rate limits
        return None
