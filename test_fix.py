#!/usr/bin/env python3
"""
Test script to verify the yt-dlp fix for signature solving and challenge solving issues.
"""

import yt_dlp
from src.services.downloader import Downloader
from src.utils.logger import logger


def test_yt_dlp_directly():
    """Test yt-dlp directly with the configurations we've added."""
    print("Testing yt-dlp directly with improved configuration...")
    
    test_url = "https://www.youtube.com/watch?v=JiFuBIH9Yyg"  # The URL from the error log
    
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": False,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "player_skip": ["hls", "dash", "webpage"],
                "skip": ["authcheck"],
            }
        },
        "extractor_retries": 3,
        "retries": 3,
        "check_formats": "selected",
        "extractor_sigs": True,
        "extractor_downloads": "all",
        "hls_prefer_native": True,
        "external_downloader": "native",
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            print(f"Successfully extracted info for: {info.get('title', 'Unknown Title')}")
            return True
    except Exception as e:
        print(f"Direct yt-dlp test failed: {e}")
        return False


def test_downloader_class():
    """Test the Downloader class with the fix."""
    print("\nTesting Downloader class with improved configuration...")
    
    downloader = Downloader("test_downloads")
    
    # Test with a known working URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    try:
        result = downloader.download_audio(test_url, subfolder="test")
        if result:
            print(f"Successfully downloaded: {result}")
            return True
        else:
            print("Download failed or returned None")
            return False
    except Exception as e:
        print(f"Downloader class test failed: {e}")
        return False


def main():
    print("Testing the yt-dlp fix for signature/challenge solving issues...\n")
    
    success_count = 0
    
    if test_yt_dlp_directly():
        success_count += 1
    else:
        print("Direct yt-dlp test failed")
    
    if test_downloader_class():
        success_count += 1
    else:
        print("Downloader class test failed")
    
    print(f"\nCompleted {success_count}/2 tests successfully")
    
    if success_count == 2:
        print("✅ All tests passed! The fix should resolve the GitHub Actions issue.")
    else:
        print("❌ Some tests failed. Further investigation may be needed.")


if __name__ == "__main__":
    main()