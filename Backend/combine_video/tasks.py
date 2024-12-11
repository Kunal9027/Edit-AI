from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, AudioFileClip, ColorClip, concatenate_videoclips, concatenate_audioclips
import numpy as np
from moviepy.config import change_settings
from pathlib import Path
import platform

# Configure moviepy to use ImageMagick for text
if platform.system() == "Windows":
    change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})
else:
    change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

def create_watermark(text, size, opacity=0.7, fontsize=30):
    """Create a semi-transparent watermark"""
    watermark = (TextClip(text, fontsize=fontsize, color='white', font='Arial-Bold')
                .set_opacity(opacity)
                .set_duration(size[2]))
    watermark = watermark.set_position(lambda t: (40, ((size[1] - watermark.h) // 2)+60))
    return watermark

def create_text_overlay(
    text, 
    size, 
    position='top',           # Can be 'top', 'bottom', or tuple of (x, y) coordinates
    fontsize=40,
    font_style='Arial-Bold', # Font family/style
    text_color='white',      # Text color
    x_offset=0,             # Additional horizontal offset
    y_offset=0              # Additional vertical offset
):
    """
    Create a text overlay with customizable positioning and styling
    
    Parameters:
    -----------
    text : str
        The text to display
    size : tuple
        (width, height, duration) of the video
    position : str or tuple
        'top', 'bottom', or tuple of (x, y) coordinates for custom positioning
    fontsize : int
        Size of the font
    font_style : str
        Font family and style (must be available in system)
    text_color : str
        Color of the text (can be color name or hex code)
    x_offset : int
        Additional horizontal offset from calculated position
    y_offset : int
        Additional vertical offset from calculated position
    """
    try:
        # Create text clip with custom styling
        text_clip = (TextClip(
            text, 
            fontsize=fontsize, 
            color=text_color, 
            font=font_style
        ).set_duration(size[2]))
        
        # Calculate position
        if isinstance(position, tuple):
            # Use exact coordinates if position is a tuple
            x_pos, y_pos = position
        else:
            # Calculate x position (centered by default)
            x_pos = (size[0] - text_clip.w) // 2
            
            # Calculate y position based on position parameter
            if position == 'top':
                y_pos = 40
            elif position == 'bottom':
                y_pos = size[1] - text_clip.h - 20
            else:  # Default to top if invalid position is provided
                y_pos = 40
        
        # Apply additional offsets
        final_x = x_pos + x_offset
        final_y = y_pos + y_offset
        
        return text_clip.set_position((final_x, final_y))
        
    except Exception as e:
        print(f"Error creating text overlay: {str(e)}")
        # Return a default text clip if there's an error
        return (TextClip(
            text,
            fontsize=40,
            color='white',
            font='Arial-Bold'
        ).set_duration(size[2])
         .set_position(('center', 'top')))

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
    text_position='top',      # New parameter
    text_fontsize=40,         # New parameter
    text_font='Arial-Bold',   # New parameter
    text_color='white',       # New parameter
    text_x_offset=0,          # New parameter
    text_y_offset=0,          # New parameter
    background_music_path=None,  # background audio
    bg_music_volume=0.3,      # background audio volume
    video1_offset=34,         # New parameter for video1 position offset
    video2_offset=34          # New parameter for video2 position offset
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
                (output_width, output_height, final_duration),
                position=text_position,
                fontsize=text_fontsize,
                font_style=text_font,
                text_color=text_color,
                x_offset=text_x_offset,
                y_offset=text_y_offset
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
            bitrate="8000k",
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

