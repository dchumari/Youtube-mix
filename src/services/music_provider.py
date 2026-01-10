import os
import random
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic
from typing import List, Dict, Any, Optional
from ..utils.logger import logger

class MusicProvider:
    """Abstract base class for music providers"""
    def get_tracks(self, playlist_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

class SpotifyProvider(MusicProvider):
    def __init__(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.error("Spotify credentials not found in environment variables.")
            raise ValueError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET. Check your .env file.")
            
        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=client_id, client_secret=client_secret
                )
            )
            logger.info("Spotify client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise

    def get_tracks(self, playlist_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches tracks from a Spotify playlist.
        Returns a list of dicts with 'name', 'artist', 'duration_ms'.
        """
        try:
            logger.info(f"Fetching playlist: {playlist_id}")
            playlist = self.sp.playlist(playlist_id)
            if not playlist:
                raise ValueError("Playlist not found")
                
            playlist_name = playlist.get("name", "Unknown Playlist")
            logger.info(f"Found playlist: {playlist_name}")

            results = self.sp.playlist_items(playlist_id, limit=limit)
            if not results:
                raise ValueError("No items found in playlist")
                
            items = results.get("items", [])
            random.shuffle(items)
            
            tracks = []
            for item in items:
                track = item.get("track")
                if not track:
                    continue
                    
                track_info = {
                    "name": track.get("name"),
                    "artist": track.get("artists")[0].get("name") if track.get("artists") else "Unknown",
                    "duration_ms": track.get("duration_ms"),
                    "spotify_url": track.get("external_urls", {}).get("spotify"),
                    "uri": track.get("uri")
                }
                tracks.append(track_info)
                
            tracks = tracks[:limit]
            logger.info(f"Retrieved {len(tracks)} tracks from Spotify.")
            return tracks

        except Exception as e:
            logger.error(f"Error fetching Spotify tracks: {e}")
            raise

class YouTubeMusicProvider:
    def __init__(self):
        try:
            self.ytm = YTMusic()
            logger.info("YouTube Music client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize YTMusic: {e}")
            raise

    def find_track_url(self, name: str, artist: str) -> Optional[str]:
        """Searches for official song on YT Music and returns the video URL."""
        query = f"{name} {artist}"
        try:
            results = self.ytm.search(query, filter="songs")
            if not results:
                logger.warning(f"No YT Music results for: {query}")
                return None
            
            video_id = results[0].get("videoId")
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Found official track: {name} -> {url}")
                return url
        except Exception as e:
            logger.error(f"YT Music search failed for {query}: {e}")
        return None
