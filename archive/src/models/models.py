from dataclasses import dataclass
from os import link
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union


class Artist(TypedDict):
    name: str
    id: str
    url: str
    thumbnail: str


class Track(TypedDict):
    id: str
    title: str
    artist: str
    artist_id: str
    album_id: str
    duration: int
    views: int
    likes: int
    release_date: str
    preview_url: str
    image_url: str
    youtube_url: str
    spotify_url: str


class Playlist(TypedDict):
    title: str
    author: str
    views: int
    duration: int
    total_songs: int
    id: str
    url: str
    thumbnail: str
    tracks: List[Track]


class Filter(TypedDict):
    type: Literal["songs", "playlists", "videos", "albums", "artist"]


class Album(TypedDict):
    name: str
    id: str
    url: str
    thumbnail: str
    total_tracks: int
    track: List[Track]
