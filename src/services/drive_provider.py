
import gdown
from pathlib import Path
from typing import List
from ..utils.logger import logger

class DriveProvider:
    def __init__(self, download_folder: str = "downloads/drive_videos"):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

    def download_videos(self, folder_url: str) -> List[Path]:
        """
        Downloads all files from a Google Drive folder.
        Returns a list of Paths to downloaded video files.
        """
        logger.info(f"Downloading videos from Drive Folder: {folder_url}")
        
        try:
            # gdown.download_folder downloads the whole folder structure
            # to the output directory.
            # quiet=False to show progress? User requested specific folder.
            
            # Note: gdown.download_folder requires the URL to be a folder URL.
            output_dir = self.download_folder
            
            # Since gdown might re-download everything, we ideally want to check if they exist?
            # functionality of gdown usually handles skipping if --continue is used? 
            # But here we are using the python api.
            # We will use the default behavior for now which overwrites or downloads.
            
            # If the user provides a file URL, this might fail. We assume folder URL.
            
            downloaded_files = gdown.download_folder(
                url=folder_url,
                output=str(output_dir),
                quiet=False,
                use_cookies=False
            )
            
            if not downloaded_files:
                logger.warning("No files downloaded from Drive folder.")
                return []
                
            # Filter for video extensions
            video_extensions = {".mp4", ".mkv", ".mov", ".avi", ".webm"}
            video_paths = []
            
            for f in downloaded_files:
                path = Path(f)
                if path.suffix.lower() in video_extensions:
                    video_paths.append(path)
                    
            logger.info(f"Retrieved {len(video_paths)} videos from Drive.")
            return video_paths

        except Exception as e:
            logger.error(f"Drive folder download failed: {e}")
            return []
