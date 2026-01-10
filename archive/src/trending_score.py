def find_trending_videos(playlist_data, top_n=None):
    """
    Find trending videos and return playlist with tracks sorted by trending score.
    Only adds 'trendingScore' field to each track, keeps everything else identical.

    Args:
        playlist_data (dict): Original playlist data
        top_n (int): Return only top N tracks (None for all)

    Returns:
        dict: Playlist with tracks sorted by trending score (descending)
    """
    if "tracks" not in playlist_data:
        print("No tracks found")
        return playlist_data

    # Create a copy to avoid modifying original (shallow copy is fine since we're not modifying nested dicts deeply)
    result_playlist = playlist_data.copy()

    # Get reference timestamp (newest in playlist)
    timestamps = [
        t.get("lastModified") for t in playlist_data["tracks"] if t.get("lastModified")
    ]
    reference_time = max(timestamps) if timestamps else 1765000000000000

    # Calculate trending scores for each track
    tracks_with_scores = []

    for track in playlist_data["tracks"]:
        try:
            # Get views
            views_str = str(track.get("viewCount", "0"))
            views = int("".join(c for c in views_str if c.isdigit()))

            # Get age (time since upload/modification)
            last_mod = int(track.get("lastModified") or reference_time)
            age_seconds = (reference_time - last_mod) / 1000000  # Convert to seconds

            # Calculate trending score (views per second)
            trending_score = views / max(age_seconds, 1)

            # Create new track with trendingScore added
            enhanced_track = track.copy()
            enhanced_track["trendingScore"] = trending_score

            tracks_with_scores.append(
                {"track": enhanced_track, "trending_score": trending_score}
            )

        except Exception:
            # If calculation fails, keep original track with score 0
            enhanced_track = track.copy()
            enhanced_track["trendingScore"] = 0
            tracks_with_scores.append({"track": enhanced_track, "trending_score": 0})

    # Sort by trending score (highest first)
    tracks_with_scores.sort(key=lambda x: x["trending_score"], reverse=True)

    # Extract sorted tracks with trendingScore
    sorted_tracks = [item["track"] for item in tracks_with_scores]

    # Apply top_n limit if specified
    if top_n is not None and top_n > 0:
        sorted_tracks = sorted_tracks[:top_n]

    # Update the result playlist with sorted tracks
    result_playlist["tracks"] = sorted_tracks

    return result_playlist


# Alternative: Minimal version that modifies in-place (if you want to keep original track order elsewhere)
def add_trending_scores(playlist_data):
    """
    Add trendingScore to each track WITHOUT sorting.
    Returns the same playlist with trendingScore field added.
    """
    if "tracks" not in playlist_data:
        return playlist_data

    result = playlist_data.copy()

    # Get reference timestamp
    timestamps = [
        t.get("lastModified") for t in playlist_data["tracks"] if t.get("lastModified")
    ]
    reference_time = max(timestamps) if timestamps else 1765000000000000

    for track in result["tracks"]:
        try:
            # Get views
            views_str = str(track.get("viewCount", "0"))
            views = int("".join(c for c in views_str if c.isdigit()))

            # Get age
            last_mod = int(track.get("lastModified") or reference_time)
            age_seconds = (reference_time - last_mod) / 1000000

            # Calculate and add trending score
            track["trendingScore"] = views / max(age_seconds, 1)
        except Exception:
            track["trendingScore"] = 0

    return result


# Helper function to sort existing trending scores
def sort_by_trending_score(playlist_data, top_n=None):
    """
    Sort playlist tracks by existing trendingScore field.
    """
    if "tracks" not in playlist_data:
        return playlist_data

    result = playlist_data.copy()

    # Make sure all tracks have trendingScore
    if not any("trendingScore" in track for track in result["tracks"]):
        result = add_trending_scores(result)

    # Sort by trendingScore (descending)
    result["tracks"].sort(key=lambda x: x.get("trendingScore", 0), reverse=False)

    # Apply top_n limit if specified
    if top_n is not None and top_n > 0:
        result["tracks"] = result["tracks"][:top_n]

    return result


# Example usage:
if __name__ == "__main__":
    import json
    import os

    json_path = os.path.join(
        os.path.dirname(__file__), "..", "utils", "search_step.json"
    )
    # Assuming 'playlist' is your data
    with open(json_path, "r") as file:
        playlist = json.load(file)

    # Get playlist with tracks sorted by trending score
    trending_playlist = find_trending_videos(playlist)

    # Or get top 10 trending
    top_10_trending = find_trending_videos(playlist, top_n=10)

    # The result has the EXACT same structure, just with trendingScore added
    print("Original fields preserved:")
    print(f"Title: {trending_playlist['title']}")
    print(f"Author: {trending_playlist['author']['name']}")
    print(f"Track count: {len(trending_playlist['tracks'])}")

    # Each track now has trendingScore
    print("\nTop 3 trending tracks:")
    for i, track in enumerate(trending_playlist["tracks"][:3], 1):
        print(f"{i}. {track['title']}")
        print(f"   Views: {track['viewCount']}")
        print(f"   Trending Score: {track['trendingScore']:.2f}")
        print(f"   Last Modified: {track.get('lastModified')}")
        print()

    # Save to file
    import json

    with open("playlist_with_trending.json", "w", encoding="utf-8") as f:
        json.dump(trending_playlist, f, indent=2, ensure_ascii=False)
