from rest_framework import serializers
from django.utils.timesince import timesince
from .models import Announcement, Notification
from cources.models import Course


# =================== Notification Serializer ===================
class NotificationSerializer(serializers.ModelSerializer):
    """Display notifications with elapsed time for frontend badges."""
    timesince = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'slug',
            'title',
            'body',
            'notification_type',
            'is_read',
            'created_at',
            'timesince'
        ]
        read_only_fields = ['slug', 'created_at', 'is_read', 'notification_type']

    def get_timesince(self, obj):
        return timesince(obj.created_at)


# =================== Announcement Serializer ===================
class AnnouncementSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    course_title = serializers.ReadOnlyField(source='course.title')
    course = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        slug_field='slug'
    )

    def get_instructor_name(self, obj):
        if obj.instructor.first_name or obj.instructor.last_name:
            return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip()
        return obj.instructor.email

    class Meta:
        model = Announcement
        fields = [
            'slug',
            'title',
            'content',
            'course',
            'course_title',
            'instructor_name',
            'created_at',
        ]
        read_only_fields = ['slug', 'created_at', 'instructor_name', 'course_title']

    def validate(self, data):
        if not data.get('course'):
            raise serializers.ValidationError({"course": "Please select a valid course slug."})
        return data


# =================== Empty Serializer ===================
class EmptySerializer(serializers.Serializer):
    """Used for actions that require no request body (e.g. mark as read)."""
    pass