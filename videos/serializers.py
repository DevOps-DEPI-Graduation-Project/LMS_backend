
from rest_framework import serializers
from .models import Video,VideoProgress


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'video_url', 'duration', 'order', 'course']
    
    
    

class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = ['student', 'video', 'watched_seconds', 'is_completed', 'updated_at']
    

