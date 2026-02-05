from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Add current dir to sys.path
sys.path.append(".")
from src.app import App

def test_graceful_failure_logic():
    with patch('src.app.SpotifyProvider'), \
         patch('src.app.YouTubeMusicProvider'), \
         patch('src.app.Downloader'), \
         patch('src.app.Mixer'), \
         patch('src.app.TwixtorProvider'), \
         patch('src.app.YoutubeUploader'), \
         patch('gdown.download_folder') as mock_gdown_folder, \
         patch('gdown.download') as mock_gdown_download, \
         patch('src.app.Path') as mock_path_class:
        
        # Mock Path instance and its exists method
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        # Mock / operator (Path / "file")
        mock_path_instance.__truediv__.return_value = mock_path_instance
        # Mock Path(str) returning our mock instance
        mock_path_class.return_value = mock_path_instance
        
        # Setup mock files
        mock_file1 = MagicMock()
        mock_file1.id = "fail_id"
        mock_file1.path = "failed_video.mp4"
        
        mock_file2 = MagicMock()
        mock_file2.id = "success_id"
        mock_file2.path = "success_video.mp4"
        
        mock_gdown_folder.return_value = [mock_file1, mock_file2]
        
        # side_effect: raise exception for fail_id, return path for success_id
        def download_side_effect(id, **kwargs):
            if id == "fail_id":
                raise Exception("Gdown Access Denied")
            return "downloads/visuals/success_video.mp4"
            
        mock_gdown_download.side_effect = download_side_effect

        app = App(channel_profile="Twenty16", video_clips=2)
        app.video_folders = "https://drive.google.com/test"
        
        # Run
        print("Starting visuals download...")
        paths = app._get_visuals_from_drive(app.video_folders)
        
        print(f"Test finished. Retrieved {len(paths)} paths.")
        
        if len(paths) == 1:
            print("\nSUCCESS: Workflow continued after one failure.")
        else:
            print(f"\nFAILURE: Logic did not handle error correctly. Paths count: {len(paths)}")

if __name__ == "__main__":
    test_graceful_failure_logic()
