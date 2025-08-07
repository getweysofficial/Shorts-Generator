
from moviepy import VideoFileClip
from moviepy.video.fx import FadeIn, FadeOut
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
import numpy as np

# Load the video clip
clip = VideoFileClip("short_1.mp4")

# Check if duration is available
if clip.duration is None:
    print("Warning: Duration not available")
else:
    print(f"Video duration: {clip.duration} seconds")

# Duration for fade effects
fade_duration = 2  # Duration in seconds for both fade-in and fade-out

# Apply video fade effects
video_with_fades = clip.with_effects([
    FadeIn(fade_duration),
    FadeOut(fade_duration)
])

from moviepy import VideoFileClip
from moviepy.video.fx import FadeIn, FadeOut
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, MultiplyVolume

# Load the video clip
clip = VideoFileClip("short_2.mp4")

# Check if duration is available
if clip.duration is None:
    print("Warning: Duration not available")
else:
    print(f"Video duration: {clip.duration} seconds")

# Duration for fade effects
fade_duration = 2  # Duration in seconds for both fade-in and fade-out

# Apply video fade effects
video_with_fades = clip.with_effects([
    FadeIn(fade_duration),
    FadeOut(fade_duration)
])

# Audio processing: start quiet, increase to normal, then decrease at end
if clip.audio is not None:
    audio = clip.audio
    
    # Create segments with different volumes
    # First 2 seconds: low volume (20%) with fade in
    start_segment = audio.subclipped(0, fade_duration).with_effects([
        MultiplyVolume(0.2),
        AudioFadeIn(fade_duration)
    ])
    
    # Middle segment: normal volume
    if clip.duration > 2 * fade_duration:
        middle_segment = audio.subclipped(fade_duration, clip.duration - fade_duration)
    else:
        middle_segment = None
    
    # Last 2 seconds: fade out to low volume (20%)
    end_segment = audio.subclipped(clip.duration - fade_duration, clip.duration).with_effects([
        AudioFadeOut(fade_duration),
        MultiplyVolume(0.2)
    ])
    
    # Combine audio segments
    if middle_segment is not None:
        from moviepy import concatenate_audioclips
        final_audio = concatenate_audioclips([start_segment, middle_segment, end_segment])
    else:
        # For very short videos
        final_audio = audio.with_effects([
            AudioFadeIn(fade_duration/2),
            AudioFadeOut(fade_duration/2),
            MultiplyVolume(0.5)
        ])
    
    # Combine video with adjusted audio
    final_clip = video_with_fades.with_audio(final_audio)
else:
    print("Warning: No audio track found in the video")
    final_clip = video_with_fades

# Write the output video
final_clip.write_videofile("output_1.mp4")

# Clean up resources
clip.close()
final_clip.close()