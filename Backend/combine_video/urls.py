# urls.py
from django.urls import path
from .views import VideoCombinerAPIView, video_combiner_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/combine-videos/', VideoCombinerAPIView.as_view(), name='combine_videos_api'),
    path('', video_combiner_view, name='video_combiner'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)