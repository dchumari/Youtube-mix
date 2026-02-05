from .uploader import SCOPES
from ..utils.logger import logger
from typing import Optional, List, Dict
import io
from googleapiclient.http import MediaIoBaseDownload
from pathlib import Path

class DriveProvider:
    def __init__(self, service):
        self.service = service

    def create_shortcut(self, file_id: str, folder_id: str, name: Optional[str] = None) -> Optional[str]:
        """
        Creates a shortcut to a file in a specific folder.
        """
        try:
            shortcut_metadata = {
                'name': name or f"Shortcut to {file_id}",
                'mimeType': 'application/vnd.google-apps.shortcut',
                'shortcutDetails': {
                    'targetId': file_id
                },
                'parents': [folder_id]
            }
            
            shortcut = self.service.files().create(
                body=shortcut_metadata,
                fields='id'
            ).execute()
            
            shortcut_id = shortcut.get('id')
            logger.info(f"Created shortcut to {file_id} in folder {folder_id}. Shortcut ID: {shortcut_id}")
            return shortcut_id
        except Exception as e:
            logger.error(f"Failed to create shortcut for {file_id}: {e}")
            return None

    def list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """
        Lists all files in a folder, resolving shortcuts to their targets.
        """
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            logger.info(f"Listing files in folder {folder_id} with query: {query}")
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, shortcutDetails)"
            ).execute()
            
            logger.info(f"Drive API returned {len(results.get('files', []))} files.")
            
            files = []
            for f in results.get('files', []):
                if f['mimeType'] == 'application/vnd.google-apps.shortcut':
                    target_id = f.get('shortcutDetails', {}).get('targetId')
                    if target_id:
                        # We use the target ID but keep the shortcut's name or target name?
                        # Let's just store the target ID and name.
                        files.append({'id': target_id, 'name': f['name'], 'is_shortcut': True})
                else:
                    files.append({'id': f['id'], 'name': f['name'], 'is_shortcut': False})
            
            return files
        except Exception as e:
            logger.error(f"Failed to list files in folder {folder_id}: {e}")
            return []

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """
        Downloads a file from Drive.
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download Progress: {int(status.progress() * 100)}%")

            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(fh.getvalue())
            
            logger.info(f"Downloaded file {file_id} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file {file_id}: {e}")
            return False

    def debug_list_all_files(self, limit: int = 10):
        """Debug method to list some files from the entire Drive."""
        try:
            results = self.service.files().list(
                pageSize=limit,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            items = results.get('files', [])
            logger.info(f"Listing first {len(items)} files in Drive:")
            for item in items:
                logger.info(f" - {item['name']} ({item['id']}) [{item['mimeType']}]")
        except Exception as e:
            logger.error(f"Debug list failed: {e}")

    def debug_check_folder(self, folder_id: str):
        """Debug method to check if a folder exists and is accessible."""
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, mimeType"
            ).execute()
            logger.info(f"Folder found: {folder['name']} ({folder['id']}) [{folder['mimeType']}]")
        except Exception as e:
            logger.error(f"Failed to fetch folder {folder_id}: {e}")
