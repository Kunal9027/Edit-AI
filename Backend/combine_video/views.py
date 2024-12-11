from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
from .tasks import combine_videos_vertically
import uuid

class VideoCombinerAPIView(APIView):
    def post(self, request):
        try:
            # Generate unique filename for uploaded files
            def get_unique_filename(filename):
                ext = filename.split('.')[-1]
                return f"{uuid.uuid4()}.{ext}"
            
            # Handle file uploads
            video1 = request.FILES.get('video1')
            video2 = request.FILES.get('video2')
            background_music = request.FILES.get('background_music')
            
            if not all([video1, video2]):
                return Response(
                    {"error": "Both videos are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create media directories if they don't exist
            input_dir = os.path.join(settings.MEDIA_ROOT, 'input_videos')
            output_dir = os.path.join(settings.MEDIA_ROOT, 'output_videos')
            os.makedirs(input_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)

            # Save uploaded files with unique names
            video1_path = os.path.join(input_dir, get_unique_filename(video1.name))
            video2_path = os.path.join(input_dir, get_unique_filename(video2.name))
            output_filename = get_unique_filename('output.mp4')
            output_path = os.path.join(output_dir, output_filename)
            
            with open(video1_path, 'wb+') as destination:
                for chunk in video1.chunks():
                    destination.write(chunk)
            
            with open(video2_path, 'wb+') as destination:
                for chunk in video2.chunks():
                    destination.write(chunk)

            background_music_path = None
            if background_music:
                background_music_path = os.path.join(input_dir, get_unique_filename(background_music.name))
                with open(background_music_path, 'wb+') as destination:
                    for chunk in background_music.chunks():
                        destination.write(chunk)

            # Get parameters from request data
            data = request.data
            
            # Parse aspect ratio into tuple of integers
            aspect_ratio_str = data.get('aspect_ratio', '16:9')
            aspect_ratio = tuple(map(int, aspect_ratio_str.split(':')))

            params = {
                'video1_path': video1_path,
                'video2_path': video2_path,
                'output_path': output_path,
                'video1_offset': int(data.get('video1_offset', 30)),
                'video2_offset': int(data.get('video2_offset', 30)),
                'target_resolution': int(data.get('target_resolution', 1024)),
                'watermark': str(data.get('watermark', '@KunalChaudhary2')),
                'watermark_opacity': float(data.get('watermark_opacity', 0.6)),
                'bg_music_volume': float(data.get('bg_music_volume', 0.2)),
                'background_music_path': background_music_path,
                'text_overlay': str(data.get('text_overlay', 'Follow for more!\nLike & Subscribe')),
                'text_color': str(data.get('text_color', '#FFD700')),
                'text_position': str(data.get('text_position', 'bottom')),
                'text_fontsize': int(data.get('text_fontsize', 50)),
                'text_font': str(data.get('text_font', 'Impact')),
                'aspect_ratio': aspect_ratio,  # Updated to use tuple
            }

            # Call the video combining function
            combine_videos_vertically(**params)
            
            # Clean up input files
            os.remove(video1_path)
            os.remove(video2_path)
            if background_music_path:
                os.remove(background_music_path)

            # Return the URL of the processed video
            output_url = f"{settings.MEDIA_URL}output_videos/{output_filename}"
            return Response({
                "message": "Video processing completed",
                "output_url": output_url
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response(
                {"error": f"Invalid input value: {str(ve)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def video_combiner_view(request):
    return render(request, 'index.html')