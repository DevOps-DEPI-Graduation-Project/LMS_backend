
from rest_framework import serializers
from .models import Video,VideoProgress


class VideoSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.title', read_only=True)  

    class Meta:
        model = Video
        fields = ['title', 'video_url', 'order', 'course']
    
    
    

class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = ['is_completed']


class CourseVideosSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['slug', 'is_completed', 'title']

    def get_is_completed(self, obj):
        user = self.context['request'].user 

        progress = VideoProgress.objects.filter(
            video=obj
        ).first()

        return progress.is_completed if progress else False