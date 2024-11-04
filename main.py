from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, AudioFileClip, ColorClip, concatenate_videoclips, concatenate_audioclips
import numpy as np
from moviepy.config import change_settings
from pathlib import Path

# Configure moviepy to use ImageMagick for text
change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

def create_watermark(text, size, opacity=0.7, fontsize=30):
    """Create a semi-transparent watermark"""
    watermark = (TextClip(text, fontsize=fontsize, color='white', font='Arial-Bold')
                .set_opacity(opacity)
                .set_duration(size[2]))
    watermark = watermark.set_position(lambda t: (40, ((size[1] - watermark.h) // 2)+60))
    return watermark

def create_text_overlay(text, size, position='top', fontsize=40):
    """Create a text overlay with animation"""
    text_clip = (TextClip(text, fontsize=fontsize, color='white', font='Arial-Bold')
                .set_duration(size[2]))
    
    if position == 'top':
        y_pos = 40
    else:
        y_pos = size[1] - text_clip.h - 20
    
    x_pos = (size[0] - text_clip.w) // 2
    return text_clip.set_position((x_pos, y_pos))
def mix_audio(video1_audio, background_music_path, duration, bg_volume=0.3):
    """
    Mix video1's audio with looping background music correctly
    """
    try:
        # Load background music
        bg_music = AudioFileClip(background_music_path)
        
        # If background music is shorter than needed duration, loop it
        if bg_music.duration < duration:
            # Calculate how many loops needed
            repeats = int(np.ceil(duration / bg_music.duration))
            bg_clips = []
            
            for _ in range(repeats):
                bg_clips.append(bg_music)
            
            # Concatenate all clips
            bg_music = concatenate_audioclips(bg_clips)
        
        # Trim to exact duration needed
        bg_music = bg_music.subclip(0, duration)
        
        # Ensure video1 audio is the correct duration
        video1_audio = video1_audio.subclip(0, duration)
        
        # Set volumes
        bg_music = bg_music.volumex(bg_volume)
        
        # Simply return the two audio clips to be composited
        return [video1_audio, bg_music]
        
    except Exception as e:
        print(f"Error mixing audio: {str(e)}")
        return [video1_audio]  # Return only original audio if mixing fails


def adjust_video2_duration(video2, target_duration):
    """Adjust video2 duration by either looping or trimming"""
    if video2.duration < target_duration:
        repeats = int(np.ceil(target_duration / video2.duration))
        clips = [video2] * repeats
        extended_video = concatenate_videoclips(clips)
        return extended_video.subclip(0, target_duration)
    else:
        return video2.subclip(0, target_duration)

def combine_videos_vertically(
    video1_path, 
    video2_path, 
    output_path, 
    target_resolution=1080, 
    aspect_ratio=(9, 16),
    watermark="",
    watermark_opacity=0.7,
    text_overlay="",
    background_music_path=None,
    bg_music_volume=0.3,
    video1_offset=34,  # New parameter for video1 position offset
    video2_offset=34   # New parameter for video2 position offset
):
    try:
        # Load videos
        video1 = VideoFileClip(video1_path)
        video2 = VideoFileClip(video2_path)
        
        # Calculate dimensions
        output_height = target_resolution
        output_width = int(output_height * aspect_ratio[0] / aspect_ratio[1])
        square_size = output_height // 2
        
        # Process videos to squares
        video1_squared = resize_to_square(video1, square_size)
        video2_squared = resize_to_square(video2, square_size)
        
        # Adjust video2 duration to match video1
        video2_squared = adjust_video2_duration(video2_squared, video1_squared.duration)
        
        # Center position calculation
        x_position = (output_width - square_size) // 2
        
        # Position videos with custom offsets
        video1_final = video1_squared.set_position((x_position, video1_offset))
        video2_final = video2_squared.set_position((x_position, square_size - video2_offset))
        
        final_duration = video1_squared.duration
        
        # Create black background
        background = ColorClip(size=(output_width, output_height), color=(0, 0, 0), duration=final_duration)
        
        # List of clips to composite
        clips = [background, video2_final, video1_final]
        
        if watermark:
            watermark_clip = create_watermark(
                watermark, 
                (output_width, output_height, final_duration),
                opacity=watermark_opacity
            )
            clips.append(watermark_clip)
        
        if text_overlay:
            text_clip = create_text_overlay(
                text_overlay,
                (output_width, output_height, final_duration)
            )
            clips.append(text_clip)
        
        # Create final composite for video
        final_video = CompositeVideoClip(clips, size=(output_width, output_height))
        
        # Handle audio mixing
        if background_music_path and Path(background_music_path).exists():
            try:
                # Get mixed audio clips
                audio_clips = mix_audio(
                    video1_squared.audio,
                    background_music_path,
                    final_duration,
                    bg_music_volume
                )
                
                # Create dummy video clips with the audio
                audio_video_clips = [
                    ColorClip(size=(1,1), color=(0,0,0), duration=final_duration)
                    .set_audio(audio_clip)
                    for audio_clip in audio_clips
                ]
                
                # Composite the audio
                final_audio = CompositeVideoClip(audio_video_clips).audio
                final_video = final_video.set_audio(final_audio)
                
            except Exception as e:
                print(f"Error with background music, using original audio: {str(e)}")
                final_video = final_video.set_audio(video1_squared.audio)
        else:
            final_video = final_video.set_audio(video1_squared.audio)
        
        # Export with optimized settings
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            preset="faster",
            threads=4,
            bitrate="4000k",
            fps=video1.fps
        )
        
    except Exception as e:
        print(f"Error processing videos: {str(e)}")
        raise
        
    finally:
        # Clean up
        try:
            video1.close()
            video2.close()
            final_video.close()
        except:
            pass

# def combine_videos_vertically(
#     video1_path, 
#     video2_path, 
#     output_path, 
#     target_resolution=1080, 
#     aspect_ratio=(9, 16),
#     watermark="",
#     watermark_opacity=0.7,
#     text_overlay="",
#     background_music_path=None,
#     bg_music_volume=0.3
# ):
#     try:
#         # Load videos
#         video1 = VideoFileClip(video1_path)
#         video2 = VideoFileClip(video2_path)
        
#         # Calculate dimensions
#         output_height = target_resolution
#         output_width = int(output_height * aspect_ratio[0] / aspect_ratio[1])
#         square_size = output_height // 2
        
#         # Process videos to squares
#         video1_squared = resize_to_square(video1, square_size)
#         video2_squared = resize_to_square(video2, square_size)
        
#         # Adjust video2 duration to match video1
#         video2_squared = adjust_video2_duration(video2_squared, video1_squared.duration)
        
#         # Center position calculation
#         x_position = (output_width - square_size) // 2
        
#         # Position videos
#         video1_final = video1_squared.set_position((x_position , 34))
#         video2_final = video2_squared.set_position((x_position, square_size - 34))
        
#         final_duration = video1_squared.duration
        
#         # Create black background
#         background = ColorClip(size=(output_width, output_height), color=(0, 0, 0), duration=final_duration)
        
#         # List of clips to composite
#         clips = [background, video2_final, video1_final]
        
#         if watermark:
#             watermark_clip = create_watermark(
#                 watermark, 
#                 (output_width, output_height, final_duration),
#                 opacity=watermark_opacity
#             )
#             clips.append(watermark_clip)
        
#         if text_overlay:
#             text_clip = create_text_overlay(
#                 text_overlay,
#                 (output_width, output_height, final_duration)
#             )
#             clips.append(text_clip)
        
#         # Create final composite for video
#         final_video = CompositeVideoClip(clips, size=(output_width, output_height))
        
#         # Handle audio mixing
#         if background_music_path and Path(background_music_path).exists():
#             try:
#                 # Get mixed audio clips
#                 audio_clips = mix_audio(
#                     video1_squared.audio,
#                     background_music_path,
#                     final_duration,
#                     bg_music_volume
#                 )
                
#                 # Create dummy video clips with the audio
#                 audio_video_clips = [
#                     ColorClip(size=(1,1), color=(0,0,0), duration=final_duration)
#                     .set_audio(audio_clip)
#                     for audio_clip in audio_clips
#                 ]
                
#                 # Composite the audio
#                 final_audio = CompositeVideoClip(audio_video_clips).audio
#                 final_video = final_video.set_audio(final_audio)
                
#             except Exception as e:
#                 print(f"Error with background music, using original audio: {str(e)}")
#                 final_video = final_video.set_audio(video1_squared.audio)
#         else:
#             final_video = final_video.set_audio(video1_squared.audio)
        
#         # Export with optimized settings
#         final_video.write_videofile(
#             output_path,
#             codec="libx264",
#             audio_codec="aac",
#             preset="faster",
#             threads=4,
#             bitrate="4000k",
#             fps=video1.fps
#         )
        
#     except Exception as e:
#         print(f"Error processing videos: {str(e)}")
#         raise
        
#     finally:
#         # Clean up
#         try:
#             video1.close()
#             video2.close()
#             final_video.close()
#         except:
#             pass


def resize_to_square(video, square_size):
    """Resize a video to a square while maintaining aspect ratio."""
    width, height = video.size
    if width > height:
        # Crop width
        crop_width = (width - height) // 2
        video = video.crop(x1=crop_width, x2=width - crop_width)
    else:
        # Crop height
        crop_height = (height - width) // 2
        video = video.crop(y1=crop_height, y2=height - crop_height)
    
    # Resize to square
    video = video.resize((square_size, square_size))
    return video

# Example usage:
combine_videos_vertically(
    "Arpit bala's Muslim joke (deleted stream).mp4",  # Main video with audio to keep
    "temp/Subway Surfer.mp4",  # Secondary video to loop/trim
    "output_with_Bgmusic.mp4",  # final output video
    video1_offset= 30,   
    video2_offset= 30,
    target_resolution=1080,     # resolution of thr final video
    watermark="@KunalChaudhary",    #video watermark
    watermark_opacity=0.6,      # watermark opacity transparency
    text_overlay="""Follow for more!
    Like & Subscribe""",        #text at the top of the video
    background_music_path="audio_test.mp3",  # Path to your background music
    bg_music_volume=0.2   # Adjust this value between 0.0 and 1.0 to control background music volume
)

# add two new peramets where i can give the video position 