from ..spotify_mix import spotify_mixer

if __name__ == "__main__":
    # spotify_mixer(, "client_secrets.json")
    spotify_mixer(
        youtube_channel_name="phonkmixxx",
        client_secrets="client_secrets.json",
        playlist_id="3mAH5gPbw4YFlYaNoGiPIX",
        mix_minutes=90,
        track_limit=100,
    )
