import random
import gc
import os
from pathlib import Path
from typing import List, Tuple
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from ..utils.logger import logger

class Mixer:
    def create_mix(self, audio_paths: List[Path], video_paths: List[Path], output_file: Path) -> Tuple[List[str], Path]:
        """
        Creates a video mix from audio tracks and video clips.
        Returns (timestamps, output_file_path).
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not audio_paths:
            raise ValueError("No audio paths provided")
        if not video_paths:
            raise ValueError("No video paths provided")

        logger.info(f"Starting mix with {len(audio_paths)} audio tracks and {len(video_paths)} video clips.")
        
        # Shuffle resources
        random.shuffle(audio_paths)
        random.shuffle(video_paths)
        
        opened_clips = []
        video_cache = {}  # Cache for unique video clips
        timestamps = []
        total_seconds = 0
        
        try:
            # 1. Prepare Audio
            audio_clips = []
            for path in audio_paths:
                try:
                    clip = AudioFileClip(str(path))
                    opened_clips.append(clip)
                    audio_clips.append(clip)
                    
                    # Track timestamps
                    start_time_str = self._seconds_to_hms(total_seconds)
                    name = path.stem.replace("_", " ")
                    timestamps.append(f"{start_time_str} - {name}")
                    
                    total_seconds += clip.duration
                except Exception as e:
                    logger.error(f"Failed to load audio {path}: {e}")

            if not audio_clips:
                raise RuntimeError("No valid audio clips loaded")

            logger.info("Concatenating audio...")
            final_audio = concatenate_audioclips(audio_clips)
            audio_duration = final_audio.duration
            logger.info(f"Total audio duration: {self._seconds_to_hms(audio_duration)}")

            # 2. Prepare Video
            # We need to loop/concatenate videos until we cover the audio duration
            video_clips_mix = []
            current_video_duration = 0
            
            while current_video_duration < audio_duration:
                v_path = random.choice(video_paths)
                v_str = str(v_path)
                
                try:
                    if v_str not in video_cache:
                        logger.info(f"Loading unique video clip: {v_path.name}")
                        clip = VideoFileClip(v_str, audio=False)
                        
                        # Resize to standard HD (720p) to prevent stride issues and save memory
                        clip = clip.resized(height=720) # Keep aspect ratio
                        
                        # Trim the very end (0.1s) to avoid "bytes wanted but 0 read" errors
                        if clip.duration > 0.1:
                            clip = clip.subclipped(0, clip.duration - 0.1)
                        
                        video_cache[v_str] = clip
                        opened_clips.append(clip)
                    else:
                        clip = video_cache[v_str]

                    video_clips_mix.append(clip)
                    current_video_duration += clip.duration
                except Exception as e:
                    logger.error(f"Failed to load video {v_path}: {e}")
                    # Remove from paths so we don't try it again
                    video_paths.remove(v_path)
                    if not video_paths:
                        break

            if not video_clips_mix:
                 raise RuntimeError("No valid video clips loaded")

            logger.info("Concatenating video...")
            final_video_raw = concatenate_videoclips(video_clips_mix, method="compose")
            
            # Trim to exact audio length
            final_video = final_video_raw.subclipped(0, audio_duration)
            
            # Combine
            logger.info("Compositing final mix...")
            final_output = final_video.with_audio(final_audio)

            # Write
            logger.info(f"Writing to {output_file}...")
            # Use a temp audio file to avoid freeze
            temp_audio = output_file.parent / "temp_audio.m4a"
            
            final_output.write_videofile(
                str(output_file),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(temp_audio.absolute()),
                remove_temp=True,
                threads=4, # Increased for speed, but will monitor
                preset="ultrafast", # Faster for testing/automation
                logger="bar"
            )
            
            return timestamps, output_file

        except Exception as e:
            logger.error(f"Mixing failed: {e}")
            raise
        finally:
            # Cleanup
            logger.info("Cleaning up resources...")
            for clip in opened_clips:
                try:
                    clip.close()
                    if hasattr(clip, 'reader'): clip.reader.close()
                    if hasattr(clip, 'audio') and clip.audio: clip.audio.close()
                except:
                    pass
            
            # Explicit GC
            gc.collect()

    def _seconds_to_hms(self, seconds):
        seconds = int(seconds)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
