from typing import Literal, Union

import requests
from ytmusicapi import YTMusic

from models import Filter, Playlist, Track

# ym = YTMusic()


class YoutubeSearch:
    """Handles raw YouTube searches using requests."""

    BASE_URL = "https://www.youtube.com/results?search_query="

    def search(self, query: str, filter: Filter) -> str:
        response = requests.get(self.BASE_URL + query)
        response.raise_for_status()
        return response.text

    def get_playlist(self, id: str) -> str:
        response = requests.get(self.BASE_URL + id)
        response.raise_for_status()
        return response.text


class YoutubeClient:
    """Unified client for YTMusic and YouTube searches."""

    def __init__(self, resource: Literal["ytmusic", "youtube"] = "ytmusic"):
        self.youtube_search = YoutubeSearch()
        self.ytmusic_client = YTMusic()
        self.resources = resource

    def tool(self):
        if self.resources == "ytmusic":
            return self.ytmusic_client
        elif self.resources == "youtube":
            return self.youtube_search
        else:
            raise ValueError("Invalid resource. Choose 'ytmusic' or 'youtube'.")

    def search(self, query: str, filter: Filter):
        return self.tool().search(query, filter=filter)

    # Optional helpers
    def search_playlists(self, query: str):
        return self.tool().search(query, filter="playlists")

    def search_songs(self, query: str):
        return self.tool().search(query, filter="songs")

    def search_artists(self, query: str):
        return self.tool().search(query, filter="artists")

    def search_albums(self, query: str):
        return self.ytmusic_client.search(query, filter="albums")

    def song_info(self, id: str):
        songs = self.ytmusic_client.search(id, filter="songs")
        return songs[0] if songs else None

    def playlist_info(self, id: str):
        return self.tool().get_playlist(id)


if __name__ == "__main__":
    import json

    client = YoutubeClient()
    # print(json.dumps(client.search_artists("playboi carti"), indent=4))
    print(
        json.dumps(
            client.playlist_info("VLPLexTdSvJjtKrdgRnpYlaoiP6c8YduTltG"), indent=4
        )
    )
