from rest_framework import serializers
from .models import Announcement, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

# =================== Announcement Serializer ===================
class AnnouncementSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.email')  # يبقى تلقائي من request.user
    specific_users = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'content',
            'target_type',
            'course',
            'specific_users',
            'sender',
            'created_at',
            'slug',
        ]
        read_only_fields = ['created_at', 'slug', 'sender']

    def validate(self, data):
        target_type = data.get('target_type')
        course = data.get('course')
        specific_users = data.get('specific_users', [])

        if target_type == 'course_students' and not course:
            raise serializers.ValidationError("Course must be selected for course_students target.")
        if target_type == 'specific_users' and not specific_users:
            raise serializers.ValidationError("You must select specific users for this target type.")
        return data


# =================== Notification Serializer ===================
class NotificationSerializer(serializers.ModelSerializer):
    announcement = serializers.ReadOnlyField(source='announcement.title')  # يظهر عنوان الـ announcement لو موجود

    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'body',
            'is_read',
            'is_sent',
            'announcement',
            'created_at',
            'slug',
        ]
        read_only_fields = ['is_read', 'is_sent', 'created_at', 'slug']