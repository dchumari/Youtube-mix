import os
import time
import socket
from pathlib import Path
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import httplib2
from google_auth_httplib2 import AuthorizedHttp
from tqdm import tqdm
import ssl

from ..utils.logger import logger

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YoutubeUploader:
    def __init__(self, profile: dict):
        self.profile = profile
        self.secrets_file = Path(profile.get("secrets_file", "config/client_secrets.json"))
        self.token_file = Path(profile.get("token_file", "config/tokens/token.json"))
        self.service = None

    def authenticate(self, headless: bool = True):
        """
        Authenticates with YouTube.
         If token exists and is valid/refreshable, uses it.
         If not, and headless=False, starts local server.
        """
        creds = None
        
        # Ensure parent dir for token exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

        # 1. Load existing token
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            except Exception as e:
                logger.error(f"Error loading token file: {e}")
                creds = None

        # 2. Check validity / Refresh
        if creds and creds.valid:
            logger.info("Using valid cached credentials.")
        elif creds and creds.expired and (creds.refresh_token or self.profile.get("refresh_token")):
            logger.info("Token expired. Refreshing...")
            try:
                # If we have a manual refresh token but existing creds don't have it, inject it
                if not creds.refresh_token and self.profile.get("refresh_token"):
                    creds.refresh_token = self.profile.get("refresh_token")
                
                creds.refresh(Request())
                # Save refreshed token
                self.token_file.write_text(creds.to_json())
                logger.info("Token refreshed and saved.")
            except Exception as e:
                error_str = str(e)
                if "invalid_grant" in error_str:
                    logger.error("Failed to refresh token: The token has been expired or revoked.")
                    logger.error("--- ACTION REQUIRED ---")
                    logger.error("1. Make sure your Google Cloud Project is set to 'In Production' (https://console.cloud.google.com/apis/credentials/consent)")
                    logger.error("2. Run 'python main.py auth' to re-authenticate.")
                    logger.error("-----------------------")
                else:
                    logger.error(f"Failed to refresh token: {e}")
                creds = None
        
        # 3. New Login (only if not headless or explicit override)
        if not creds and self.profile.get("refresh_token"):
            logger.info("Attempting authentication using manual refresh token from settings...")
            try:
                # Create credentials from refresh token
                import json
                with open(self.secrets_file, "r") as f:
                    client_config = json.load(f)
                
                creds = Credentials(
                    token=None,
                    refresh_token=self.profile.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_config["installed"]["client_id"],
                    client_secret=client_config["installed"]["client_secret"],
                    scopes=SCOPES
                )
                creds.refresh(Request())
                self.token_file.write_text(creds.to_json())
                logger.info("Successfully authenticated with manual refresh token.")
            except Exception as e:
                logger.error(f"Manual refresh token auth failed: {e}")
                creds = None

        if not creds:
            if headless:
                 # In headless mode, we cannot open a browser. We must fail.
                 # BUT, the user said "only manual intervention when setting up".
                 # So we assume setup happens via a specific CLI command (not headless).
                 logger.error("No valid token found and running in headless mode. Please run 'python main.py auth' first.")
                 raise RuntimeError("Authentication required. Run setup first.")
            else:
                logger.info("Initiating new authentication flow...")
                if not self.secrets_file.exists():
                    raise FileNotFoundError(f"Secrets file not found: {self.secrets_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(str(self.secrets_file), SCOPES)
                
                # Dynamic port to avoid conflicts
                # Access_type offline is crucial for refresh token
                creds = flow.run_local_server(
                    port=0, 
                    access_type="offline", 
                    prompt="consent"
                )
                
                self.token_file.write_text(creds.to_json())
                logger.info(f"Authentication successful. Token saved to {self.token_file}")

        # Build Service
        # Increased timeout to handle large uploads and potential network hiccups
        http = httplib2.Http(timeout=600)
        
        # 🔥 CRITICAL: disable redirect following. 
        # The YouTube Resumable upload sends 308 redirects which httplib2 
        # sometimes tries to follow incorrectly, leading to "Missing Location header" errors.
        http.follow_redirects = False
        
        authed_http = AuthorizedHttp(creds, http=http)
        self.service = build("youtube", "v3", http=authed_http, cache_discovery=False)
        return self.service

    def upload_video(
        self, 
        file_path: Path, 
        title: str, 
        description: str, 
        tags: List[str], 
        privacy_status: str = "public",
        thumbnail_path: Optional[Path] = None
    ):
        if not self.service:
            self.authenticate(headless=True)

        logger.info(f"Uploading video: {title}")
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "10",  # Music
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
        
        # We use a context manager and MediaIoBaseUpload to ensure the file handle is 
        # properly closed even if the upload fails. This prevents WinError 32 during cleanup.
        file_size = file_path.stat().st_size
        with open(file_path, "rb") as f:
            # Using smaller chunks (2MB) as per the working archive implementation.
            # This is more stable for long uploads and handles SSL/Timeout issues better.
            CHUNK_SIZE = 2 * 1024 * 1024
            media = MediaIoBaseUpload(f, mimetype="video/*", chunksize=CHUNK_SIZE, resumable=True)
            
            request = self.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = None
            retries = 0
            
            # Use tqdm for a nice progress meter
            pbar = tqdm(total=100, desc="Uploading to YouTube", unit="%")
            last_progress = 0
            
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        pbar.update(progress - last_progress)
                        last_progress = progress
                except (ssl.SSLEOFError, ConnectionResetError, TimeoutError, socket.timeout) as e:
                    retries += 1
                    logger.warning(f"Network error during upload (Retry {retries}/15): {e}")
                    if retries > 15: 
                        pbar.close()
                        raise
                    time.sleep(5)
                    continue
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        logger.warning(f"Temporary server error {e.resp.status}. Retrying...")
                        time.sleep(5)
                        retries += 1
                        if retries > 15: 
                            pbar.close()
                            raise
                        continue
                    else:
                        pbar.close()
                        raise
                except Exception as e:
                    logger.warning(f"Upload error: {e}. Retrying...")
                    retries += 1
                    if retries > 15: 
                        pbar.close()
                        raise
                    time.sleep(5)
                    continue
            
            pbar.n = 100
            pbar.refresh()
            pbar.close()

            video_id = response.get("id")
        logger.info(f"Upload Complete! Video ID: {video_id}")
        
        if thumbnail_path and thumbnail_path.exists():
            self._upload_thumbnail(video_id, thumbnail_path)
            
        return video_id

    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path):
        try:
            logger.info("Uploading thumbnail...")
            self.service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path))
            ).execute()
            logger.info("Thumbnail uploaded.")
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
