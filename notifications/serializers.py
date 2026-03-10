from rest_framework import serializers
from .models import Announcement, Notification
from cources.models import Course  # Ensure correct app name (cources/courses)

# =================== Announcement Serializer ===================
class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Serializer to manage Course Announcements.
    Uses 'course slug' instead of 'ID' for identification.
    """
    instructor_name = serializers.ReadOnlyField(source='instructor.get_full_name')
    course_title = serializers.ReadOnlyField(source='course.title')
    
    # Identify course by its slug in the request/response
    course = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        slug_field='slug'
    )

    class Meta:
        model = Announcement
        fields = [
            'slug',
            'title',
            'content',
            'course',        # This will now expect/return the course slug
            'course_title',
            'instructor_name',
            'created_at',
        ]
        read_only_fields = [
            'slug', 
            'created_at', 
            'instructor_name', 
            'course_title'
        ]

    def validate(self, data):
        """
        Check that the course field is provided during creation.
        """
        if not data.get('course'):
            raise serializers.ValidationError({"course": "Please select a valid course slug."})
        return data


# =================== Notification Serializer ===================
class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer to represent user notifications.
    Provides detailed info about the notification type and read status.
    """
    class Meta:
        model = Notification
        fields = [
            'slug',
            'title',
            'body',
            'is_read',
            'notification_type',
            'created_at',
        ]
        read_only_fields = [
            'slug', 
            'created_at', 
            'is_read', 
            'notification_type'
        ]