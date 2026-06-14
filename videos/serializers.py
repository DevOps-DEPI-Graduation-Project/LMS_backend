from rest_framework import serializers
from .models import Video, VideoProgress
from cources.models import Course

class VideoSerializer(serializers.ModelSerializer):
    # Enforce SEO-friendly slug binding from the parent course model descriptor
    course = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Course.objects.all()
    )

    class Meta:
        model = Video
        fields = ['slug', 'title', 'video_url', 'video_upload', 'duration', 'order', 'status', 'course']
        # FIX: Secured calculations against manual direct API payload parameter injection vulnerabilities
        read_only_fields = ['slug', 'duration', 'order', 'status']


class VideoProgressSerializer(serializers.ModelSerializer):
    video_slug = serializers.CharField(source='video.slug', read_only=True)
    video_title = serializers.CharField(source='video.title', read_only=True)

    class Meta:
        model = VideoProgress
        fields = ['video_slug', 'video_title', 'is_completed', 'watched_seconds', 'updated_at']


class CourseVideosSerializer(serializers.ModelSerializer):
    # FIX: Transitioned from an active SerializerMethodField database hit to a performance-optimized BooleanField.
    # The value will be computed instantly inside the View using annotated pre-fetched database contexts.
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Video
        fields = ['slug', 'title', 'video_url', 'video_upload', 'order', 'duration', 'status', 'is_completed']