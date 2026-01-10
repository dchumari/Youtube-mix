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
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["webpage", "configs"],
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
            # SAFE FORMAT (no SABR, no PO token)
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "cachedir": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "player_skip": ["webpage", "configs"],
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
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download {url} after {max_retries} attempts.")
                    return None
                time.sleep(10)  # Wait longer between retries to avoid rate limits
        return None
