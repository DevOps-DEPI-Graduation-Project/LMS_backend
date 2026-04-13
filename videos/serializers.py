
from rest_framework import serializers
from .models import Video,VideoProgress


class VideoSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.title', read_only=True)  

    class Meta:
        model = Video
        fields = ['slug', 'title', 'video_url', 'video_upload', 'order', 'course']
        extra_kwargs = {
           'order': {'required': False},
        }

class VideoProgressSerializer(serializers.ModelSerializer):
    video_slug = serializers.CharField(source='video.slug', read_only=True)
    video_title = serializers.CharField(source='video.title', read_only=True)
    class Meta:
        model = VideoProgress
        fields = ['video_slug', 'video_title', 'is_completed', 'watched_seconds', 'updated_at']


class CourseVideosSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['slug', 'is_completed', 'title', 'video_url', 'video_upload', 'order','duration']

    def get_is_completed(self, obj):
        user = self.context['request'].user
        student = getattr(user, 'student_profile', None)

        if not student:
            return False

        progress = VideoProgress.objects.filter(
            video=obj,
            student=student 
        ).first()

        return progress.is_completed if progress else False