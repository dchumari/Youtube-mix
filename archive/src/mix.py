# mix.py  – 100% safe, clean, and Pyright-approved version
import gc
import glob
import os
import random
import time
from pathlib import Path

import moviepy as mp
from moviepy import (
    AudioFileClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)

from .file_manager import clean_up


def seconds_to_hms(seconds):
    seconds = int(seconds)  # remove milliseconds
    hms = f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
    return str(hms)


def make_mix(folder_path: str | Path):
    folder_path = Path(folder_path)

    if not folder_path.is_dir():
        print("\nFolder does not exist!")
        return False

    video_files = list(folder_path.glob("*.mp4"))
    if not video_files:
        print("\nNo .mp4 files found in the folder!")
        return False

    print(f"\nFound {len(video_files)} videos. Loading and shuffling...")

    random.shuffle(video_files)

    clips = []
    final_clip = None  # ← explicitly declare so it's always defined
    time_stamps = []

    total_in_sec = 0

    try:
        # Load all clips
        for video_file in video_files:
            try:
                clip = mp.VideoFileClip(str(video_file))
                clips.append(clip)

                name = video_file.name
                time_in_sec = clip.duration

                chapter = seconds_to_hms(total_in_sec)
                time_stamp = chapter + " - " + name.removesuffix(".mp4")
                time_stamps.append(time_stamp)
                total_in_sec += time_in_sec

            except Exception as e:
                print(f"Failed to load {video_file.name}: {e}")

        if not clips:
            print("No valid video clips could be loaded.")
            return False

        print("Concatenating clips...")
        final_clip = mp.concatenate_videoclips(clips, method="compose")

        output_dir = folder_path / "mix"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{folder_path.name}.mp4"
        mix_file = output_file.resolve()

        print(f"Writing final mix → {mix_file}")
        final_clip.write_videofile(
            str(mix_file),
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            threads=8,
            preset="medium",
            logger="bar",  # set to 'bar' if you want a progress bar
        )

        print("Mix created successfully!")
        return time_stamps, mix_file

    except Exception as e:
        print(f"\nError during mixing: {e}")
        return False

    finally:
        # Close every clip that was successfully opened
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass

        # Close final_clip only if it was created
        if final_clip is not None:
            try:
                final_clip.close()
            except Exception:
                pass

        if folder_path.exists():
            clean_up(folder_path, extension="mp4")
        print("All MoviePy clips safely closed.")


def safer_make_mix(playlist_folder):
    """Create mix with proper memory management"""
    video_files = list(playlist_folder.glob("*.mp4"))
    all_clips = []

    # Phase 1: Load in small batches
    batch_size = 5
    for i in range(0, len(video_files), batch_size):
        batch = video_files[i : i + batch_size]
        batch_clips = []

        print(
            f"\nProcessing batch {i // batch_size + 1}/{(len(video_files) + batch_size - 1) // batch_size}"
        )

        for video_path in batch:
            try:
                # Force garbage collection before each load
                gc.collect()

                # Load video with explicit close management
                clip = VideoFileClip(str(video_path))

                # Optional: Reduce memory by lowering quality
                if clip.size[0] * clip.size[1] > 1280 * 720:  # If > HD
                    clip = clip.resize(0.5)

                batch_clips.append(clip)
                print(f"✓ {os.path.basename(video_path)}")

            except Exception as e:
                print(f"✗ Failed: {os.path.basename(video_path)} - {e}")
                continue

        # Process this batch
        if batch_clips:
            try:
                # Concatenate batch
                batch_concatenated = concatenate_videoclips(
                    batch_clips, method="compose"
                )
                all_clips.append(batch_concatenated)

                print(f"Batch concatenated successfully")

                # CRITICAL: Close individual clips immediately
                for clip in batch_clips:
                    clip.close()
                    clip.reader.close()  # Close the reader explicitly

                # Force GC to release memory
                gc.collect()

            except Exception as e:
                print(f"Batch processing error: {e}")
                continue

    # Phase 2: Concatenate all batches
    if not all_clips:
        print("No clips loaded successfully")
        return None

    print(f"\nFinal concatenation of {len(all_clips)} batches...")

    try:
        final_mix = concatenate_videoclips(all_clips, method="compose")

        # Generate timestamps (your existing code)
        timestamps = []  # Your timestamp generation logic

        # Save the final mix
        output_file = playlist_folder.parent / f"{playlist_folder.name}_final_mix.mp4"
        final_mix.write_videofile(str(output_file), codec="libx264", audio_codec="aac")

        # Close everything
        final_mix.close()
        for clip in all_clips:
            clip.close()

        # Final memory cleanup
        gc.collect()

        return timestamps, output_file

    except Exception as e:
        print(f"Final concatenation failed: {e}")

        # Emergency cleanup
        for clip in all_clips:
            try:
                clip.close()
            except:
                pass

        gc.collect()
        return None


# Assuming your JSON data is stored in a variable called `data`
# If you have it as a string, parse it first: data = json.loads(your_json_string)


def safe_make_mix(playlist_folder):
    """Create mix with proper memory management"""
    video_files = list(playlist_folder.glob("*.mp4"))
    all_clips = []

    # Phase 1: Load in small batches
    batch_size = 5
    for i in range(0, len(video_files), batch_size):
        batch = video_files[i : i + batch_size]
        batch_clips = []

        print(
            f"\nProcessing batch {i // batch_size + 1}/{(len(video_files) + batch_size - 1) // batch_size}"
        )

        for video_path in batch:
            try:
                # Force garbage collection before each load
                gc.collect()

                # Load video with explicit close management
                clip = VideoFileClip(str(video_path))

                # Optional: Reduce memory by lowering quality
                if clip.size[0] * clip.size[1] > 1280 * 720:  # If > HD
                    clip = clip.resize(0.5)

                batch_clips.append(clip)
                print(f"✓ {os.path.basename(video_path)}")

            except Exception as e:
                print(f"✗ Failed: {os.path.basename(video_path)} - {e}")
                continue

        # Process this batch
        if batch_clips:
            try:
                # Concatenate batch
                batch_concatenated = concatenate_videoclips(
                    batch_clips, method="compose"
                )
                all_clips.append(batch_concatenated)

                print("Batch concatenated successfully")

                # CRITICAL: Close individual clips immediately
                for clip in batch_clips:
                    clip.close()
                    clip.reader.close()  # Close the reader explicitly

                # Force GC to release memory
                gc.collect()

            except Exception as e:
                print(f"Batch processing error: {e}")
                continue

    # Phase 2: Concatenate all batches
    if not all_clips:
        print("No clips loaded successfully")
        return None

    print(f"\nFinal concatenation of {len(all_clips)} batches...")

    try:
        final_mix = concatenate_videoclips(all_clips, method="compose")

        # Generate timestamps (your existing code)
        timestamps = []  # Your timestamp generation logic

        # Save the final mix
        output_file = playlist_folder.parent / f"{playlist_folder.name}_final_mix.mp4"
        final_mix.write_videofile(str(output_file), codec="libx264", audio_codec="aac")

        # Close everything
        final_mix.close()
        for clip in all_clips:
            clip.close()

        # Final memory cleanup
        gc.collect()

        return timestamps, output_file

    except Exception as e:
        print(f"Final concatenation failed: {e}")

        # Emergency cleanup
        for clip in all_clips:
            try:
                clip.close()
            except:
                pass

        gc.collect()
        return None


def make_custom_mix(playlist_folder, video_folder):
    playlist_folder = Path(playlist_folder)
    video_folder = Path(video_folder)

    opened_clips = []

    if not playlist_folder.is_dir():
        print("\nFolder does not exist!")
        return False

    if not video_folder.is_dir():
        print("\nFolder does not exist!")
        return False

    audio_files = list(playlist_folder.glob("*.mp3"))
    if not audio_files:
        print("\nNo mp3 files found in the folder!")
        return False

    video_files = list(video_folder.glob("*.mp4"))
    if not video_files:
        print("\nNo .mp4 files found in the folder!")
        return False

    print(f"\nFound {len(video_files)} videos. Loading and shuffling...")
    random.shuffle(video_files)
    print(f"\nFound {len(audio_files)} audio. Loading and shuffling...")
    random.shuffle(audio_files)

    clips = []
    final_mix = None  # ← explicitly declare so it's always defined
    time_stamps = []
    audio_clips = []
    # 2. Add Video Clips
    total_in_sec = 0

    try:
        # 4. Concatenate and Save
        output_dir = playlist_folder / "mix"
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{playlist_folder.name}.mp4"
        mix_file = output_file.resolve()

        # 3. Add Audio Clips (with a black background for the visual)

        for audio_path in audio_files:
            try:
                audio = AudioFileClip(audio_path)
                opened_clips.append(audio)
                audio_clips.append(audio)

                name = audio_path.stem
                time_in_sec = audio.duration

                chapter = seconds_to_hms(total_in_sec)

                time_stamp = chapter + " - " + name
                time_stamps.append(time_stamp)
                total_in_sec += time_in_sec

            except Exception as e:
                print(f"Failed to load {audio_path}: {e}")

        try:
            temp_audio_path = "temp_final_audio.mp3"
            audio_mix = concatenate_audioclips(audio_clips)

            audio_mix.write_audiofile(temp_audio_path)
            final_audio_mix = AudioFileClip(temp_audio_path)

        except Exception as e:
            raise Exception(f"Failed to concatenate audio clips: {e}")

        try:
            print("\nAdding video files...")
            mix_clips = []
            current_video_duration = 0
            audio_duration = audio_mix.duration

            # Continue adding clips until they match or exceed the audio duration
            while current_video_duration < audio_duration:
                # 1. Select a random path from your list of video file paths
                video_path = random.choice(video_files)

                # 2. Load it as a MoviePy object
                clip = VideoFileClip(
                    str(video_path), target_resolution=(1080, 1920), audio=False
                )
                current_video_duration += clip.duration

                # 3. Add the object to your list and update total duration
                opened_clips.append(clip)
                mix_clips.append(clip)

            # 4. Combine all individual clips into one single video object
            final_video_mix = concatenate_videoclips(mix_clips, method="compose")

            # 5. Trim the video to exactly match the audio if it's slightly longer
            final_video_mix = final_video_mix.subclipped(0, audio_duration)

            print("Mix finnished")

        except Exception as e:
            raise Exception(f"\nFAILED TO CREATE VIDEO MIX:\n{e}")

        try:
            print("\nMixing audio files...")
            # audio_mix = concatenate_audioclips(audio_clips)
            # video_mix = concatenate_videoclips(mix_clips, method="compose")
            # final_mix = video_mix.with_audio(audio_mix)
            # video_mix = concatenate_videoclips(mix_clips, method="compose")
            final_mix = final_video_mix.with_audio(final_audio_mix)
            final_mix.write_videofile(
                str(mix_file),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                threads=8,
                preset="medium",
                logger="bar",  # set to 'bar' if you want a progress bar
            )

        except Exception as e:
            raise Exception(f"Failed to concatenate: {e}")

        return time_stamps, mix_file

    except Exception as e:
        print(f"\nError during mixing: {e}")
        return False

    finally:
        for clip in opened_clips:
            try:
                clip.close()
            except Exception:
                pass

        try:
            if final_mix:
                final_mix.close()
        except Exception:
            pass

        # Give Windows time to release file handles
        time.sleep(2)

        import gc

        gc.collect()
        time.sleep(2)

        print("All MoviePy clips safely closed.")


def calculate_duration(data):
    total_seconds = 0

    for track in data["tracks"]:
        # Check if "lengthSeconds" key exists and is not null
        if track and "lengthSeconds" in track and track["lengthSeconds"]:
            try:
                total_seconds += int(track["lengthSeconds"])
            except (ValueError, TypeError):
                # Handle cases where lengthSeconds might not be a valid integer string
                print(f"Skipping invalid lengthSeconds: {track.get('lengthSeconds')}")

    print(f"Total seconds: {total_seconds}")

    # Optional: Convert to hours, minutes, seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    print(f"Total duration: {hours}h {minutes}m {seconds}s")
    return minutes
