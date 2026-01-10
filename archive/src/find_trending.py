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

    # Create a copy to avoid modifying original
    result_playlist = playlist_data.copy()

    # Get current time in the same format as lastModified (microseconds since epoch)
    import time

    current_time_microseconds = int(
        time.time() * 1000000
    )  # Current time in microseconds

    # Calculate trending scores for each track
    tracks_with_scores = []

    for track in playlist_data["tracks"]:
        try:
            # Get views - handle both string with commas and integers
            views_str = str(track.get("viewCount", "0"))
            # Remove commas and any non-digit characters
            views = int("".join(filter(str.isdigit, views_str)))

            # Get last modified timestamp
            last_mod = track.get("lastModified")
            if not last_mod:
                # If no lastModified, use a very old date (1 year ago)
                last_mod = current_time_microseconds - (365 * 24 * 3600 * 1000000)
            else:
                last_mod = int(last_mod)

            # Calculate age in SECONDS (not microseconds!)
            # Convert microseconds to seconds: divide by 1,000,000
            age_seconds = (current_time_microseconds - last_mod) / 1000000.0

            # Ensure age is at least 1 second to avoid division by zero
            if age_seconds < 1:
                age_seconds = 1

            # Calculate trending score (views per second)
            trending_score = views / age_seconds

            # DEBUG: Print calculation for first few tracks
            if len(tracks_with_scores) < 3:
                print(f"DEBUG: {track['title'][:30]}...")
                print(f"  Views: {views:,}")
                print(f"  Last Mod: {last_mod}")
                print(f"  Age (days): {age_seconds / 86400:.2f}")
                print(f"  Trending Score: {trending_score:.2f}\n")

            # Create new track with trendingScore added
            enhanced_track = track.copy()
            enhanced_track["trendingScore"] = trending_score

            tracks_with_scores.append(
                {"track": enhanced_track, "trending_score": trending_score}
            )

        except Exception as e:
            print(f"Error calculating score for {track.get('title', 'Unknown')}: {e}")
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


# Even better: Use days instead of seconds for more readable scores
def find_trending_videos_days(playlist_data, top_n=None):
    """
    Alternative: Calculate trending as views per day (more intuitive).
    """
    if "tracks" not in playlist_data:
        print("No tracks found")
        return playlist_data

    import copy
    import time

    result_playlist = copy.deepcopy(playlist_data)
    current_time_microseconds = int(time.time() * 1000000)

    tracks_with_scores = []

    for track in playlist_data["tracks"]:
        try:
            # Get views
            views_str = str(track.get("viewCount", "0"))
            views = int("".join(filter(str.isdigit, views_str)))

            # Get last modified
            last_mod = track.get("lastModified")
            if not last_mod:
                last_mod = current_time_microseconds - (365 * 24 * 3600 * 1000000)
            else:
                last_mod = int(last_mod)

            # Calculate age in DAYS
            age_days = (current_time_microseconds - last_mod) / (1000000.0 * 86400)

            # Ensure minimum age
            if age_days < 0.1:  # Less than 2.4 hours
                age_days = 0.1

            # Calculate trending score (views per day)
            trending_score = views / age_days

            enhanced_track = track.copy()
            enhanced_track["trendingScore"] = trending_score
            enhanced_track["ageDays"] = age_days  # Optional: add age for reference

            tracks_with_scores.append(
                {"track": enhanced_track, "trending_score": trending_score}
            )

        except Exception:
            enhanced_track = track.copy()
            enhanced_track["trendingScore"] = 0
            tracks_with_scores.append({"track": enhanced_track, "trending_score": 0})

    # Sort
    tracks_with_scores.sort(key=lambda x: x["trending_score"], reverse=True)
    sorted_tracks = [item["track"] for item in tracks_with_scores]

    if top_n:
        sorted_tracks = sorted_tracks[:top_n]

    result_playlist["tracks"] = sorted_tracks
    return result_playlist


# Simple debug function to see what's happening
def debug_trending_calculation(playlist_data):
    """Debug the trending calculation."""
    import time

    print("DEBUGGING TRENDING CALCULATION")
    print("=" * 60)

    current_time_microseconds = int(time.time() * 1000000)
    print(f"Current time (microseconds): {current_time_microseconds}")
    print(f"Current time (readable): {time.ctime()}")

    for i, track in enumerate(playlist_data["tracks"]):
        print(f"\nTrack {i + 1}: {track['title'][:40]}...")
        print(f"  Views: {track.get('viewCount')}")
        print(f"  Last Modified: {track.get('lastModified')}")

        if track.get("lastModified"):
            last_mod = int(track["lastModified"])
            age_seconds = (current_time_microseconds - last_mod) / 1000000.0
            age_days = age_seconds / 86400

            # Try to parse views
            try:
                views_str = str(track.get("viewCount", "0"))
                views = int("".join(filter(str.isdigit, views_str)))

                print(f"  Views (parsed): {views:,}")
                print(f"  Age (seconds): {age_seconds:,.0f}")
                print(f"  Age (days): {age_days:.2f}")

                if age_seconds > 0:
                    score_per_second = views / age_seconds
                    score_per_day = views / age_days
                    print(f"  Score (views/sec): {score_per_second:.2f}")
                    print(f"  Score (views/day): {score_per_day:,.0f}")
            except Exception as e:
                print(f"  Error parsing: {e}")


# Test with your data
if __name__ == "__main__":
    # Assuming 'playlist' is your data
    playlist = {...}  # Your JSON data here

    # First debug
    debug_trending_calculation(playlist)

    # Then calculate trending
    trending_playlist = find_trending_videos(playlist)

    # Or use the days version (better for readability)
    trending_playlist_days = find_trending_videos_days(playlist)

    # Check results
    print("\n" + "=" * 60)
    print("TOP TRENDING TRACKS (views per day):")
    for i, track in enumerate(trending_playlist_days["tracks"][:5], 1):
        title = (
            track["title"][:50] + "..." if len(track["title"]) > 50 else track["title"]
        )
        score = track.get("trendingScore", 0)
        print(f"{i}. {title}")
        print(f"   Score: {score:,.0f} views/day")
        print(f"   Views: {track.get('viewCount')}")
        if "ageDays" in track:
            print(f"   Age: {track['ageDays']:.1f} days")
        print()
