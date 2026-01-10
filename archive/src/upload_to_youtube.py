import os
import ssl
import time
from pathlib import Path

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

path = Path(__file__).parent

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = path / "config" / "client_secrets.json"
CLIENT_SECRETS_FOLDER = path / "config" / "client_secrets"
CLIENT_SECRETS_FOLDER.mkdir(parents=True, exist_ok=True)
# TOKEN_FILE = path / "config" / "tokens" / "token.json"  # <-- Save token here


# def get_authenticated_service(channel_name, client_secrets_file_name):
#     creds = None

#     if client_secrets_file_name.endswith(".json"):
#         client_secrets_file = CLIENT_SECRETS_FOLDER / client_secrets_file_name
#     else:
#         client_secrets_file = CLIENT_SECRETS_FOLDER / f"{client_secrets_file_name}.json"

#     TOKEN_FILE = (
#         path / "config" / "tokens" / f"{channel_name}_token.json"
#     )  # <-- Save token here

#     if not client_secrets_file.exists():
#         raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")

#     # Load saved credentials
#     if TOKEN_FILE.exists():
#         creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
#             TOKEN_FILE, SCOPES
#         )

#     # If no valid credentials, do login flow
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 client_secrets_file, SCOPES
#             )
#             creds = flow.run_local_server(
#                 port=8080, access_type="offline", prompt="consent"
#             )

#         TOKEN_FILE.write_text(creds.to_json())

#     return build("youtube", "v3", credentials=creds)

import httplib2
from google.auth.exceptions import RefreshError
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build


def build_youtube(creds):
    http = httplib2.Http(timeout=300, disable_ssl_certificate_validation=False)

    # 🔥 CRITICAL: disable redirect following
    http.follow_redirects = False

    authed_http = AuthorizedHttp(creds, http=http)

    return build("youtube", "v3", http=authed_http, cache_discovery=False)


# def get_authenticated_service(channel_name, client_secrets_file_name):
#     creds = None

#     if client_secrets_file_name.endswith(".json"):
#         client_secrets_file = CLIENT_SECRETS_FOLDER / client_secrets_file_name
#     else:
#         client_secrets_file = CLIENT_SECRETS_FOLDER / f"{client_secrets_file_name}.json"

#     TOKEN_FILE = path / "config" / "tokens" / f"{channel_name}_token.json"
#     TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

#     if TOKEN_FILE.exists():
#         creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
#             TOKEN_FILE, SCOPES
#         )

#     if not creds or not creds.valid:
#         try:
#             if creds and creds.expired and creds.refresh_token:
#                 print("🔄 Refreshing access token...")
#                 creds.refresh(Request())
#             else:
#                 raise RefreshError("No valid refresh token")

#         except RefreshError:
#             print("⚠️ Token invalid or revoked. Re-authenticating...")

#             if TOKEN_FILE.exists():
#                 TOKEN_FILE.unlink()  # delete bad token

#             flow = InstalledAppFlow.from_client_secrets_file(
#                 client_secrets_file, SCOPES
#             )

#             creds = flow.run_local_server(port=8080, access_type="offline")

#         TOKEN_FILE.write_text(creds.to_json())

#     return build_youtube(creds)


def get_authenticated_service(channel_name, client_secrets_file_name):
    creds = None

    if client_secrets_file_name.endswith(".json"):
        client_secrets_file = CLIENT_SECRETS_FOLDER / client_secrets_file_name
    else:
        client_secrets_file = CLIENT_SECRETS_FOLDER / f"{client_secrets_file_name}.json"

    # Path for your saved token
    token_file = path / "config" / "tokens" / f"{channel_name}_token.json"

    # Load existing credentials if they exist
    if token_file.exists():
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
            str(token_file), SCOPES
        )

    # Validate or Refresh
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                print(f"🔄 Attempting to refresh token for {channel_name}...")
                creds.refresh(Request())
            else:
                # No refresh token available, must trigger a new flow
                raise RefreshError("No refresh token found")

        except RefreshError:
            print(
                "⚠️ Token expired or revoked. Opening browser for re-authentication..."
            )

            if token_file.exists():
                token_file.unlink()

            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_file), SCOPES
            )

            # FIX: Set port=0 to avoid "address already in use" errors
            # prompt="consent" ensures you get a new refresh token
            creds = flow.run_local_server(
                port=0, access_type="offline", prompt="consent"
            )

            token_file.write_text(creds.to_json())

    return build_youtube(creds)


def upload_video(
    youtube, video_file, title, description, tags=None, privacy="public", thumbnail=None
):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "10",  # Music category
        },
        "status": {"privacyStatus": privacy},
        "madeForKids": False,  # <-- Set TRUE or FALSE
    }

    # Use small 4 MB chunks (fixes SSL EOF errors)
    CHUNK_SIZE = 2 * 1024 * 1024

    media = MediaFileUpload(video_file, chunksize=CHUNK_SIZE, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )

    response = None

    # Retry logic
    MAX_RETRIES = 10
    retry = 0

    print("🚀 Upload started...")

    while response is None:
        try:
            status, response = request.next_chunk()

            if status:
                print(f"📤 Upload progress: {int(status.progress() * 100)}%")

        except (ssl.SSLEOFError, ConnectionResetError, TimeoutError) as e:
            retry += 1
            print(f"[Retry {retry}/{MAX_RETRIES}] {e}")

            if retry > MAX_RETRIES:
                raise RuntimeError("Upload failed after maximum retries") from e

            time.sleep(5)

            # 🔥 RECREATE request (important)
            request = youtube.videos().insert(
                part="snippet,status", body=body, media_body=media
            )
            continue

        except HttpError as e:
            retry += 1
            if e.resp.status in [500, 502, 503, 504]:
                print(f"[Retry {retry}/{MAX_RETRIES}] Server error {e.resp.status}")
                time.sleep(2)
                continue
            raise

    print("\nUpload complete! Video ID:", response["id"])

    if thumbnail:
        youtube.thumbnails().set(
            videoId=response["id"], media_body=MediaFileUpload(thumbnail)
        ).execute()

    return response


if __name__ == "__main__":
    youtube = get_authenticated_service(
        "phonkmixxx", client_secrets_file_name="client_secrets.json"
    )

    video_file = r"D:\Projects\AUTOMATIONS\YOUTUBE\Youtube_Music_Mix\downloads\AURA_MUSIC_PLAYLIST\mix\AURA_MUSIC_PLAYLIST.mp4"
    title = "My Music Mix"
    description = "A mix of my favorite songs."
    tags = ["music", "mix", "youtube"]

    upload_video(youtube, video_file, title, description, tags)
