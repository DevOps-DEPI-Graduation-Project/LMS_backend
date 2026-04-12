from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema, no_body

from .models import Announcement, Notification
from .serializers import AnnouncementSerializer, NotificationSerializer
from users.permissions import IsInstructorOrAdmin


def build_response(success, status_code, message, data=None):
    return Response(
        {
            "successes": success,
            "states": status_code,
            "messages": message,
            "data": data
        },
        status=status_code
    )


class AnnouncementBaseAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related('instructor', 'course')
        if user.role == 'admin':
            return queryset.all()
        return queryset.filter(instructor=user)

    def get_object(self, slug):
        return get_object_or_404(self.get_queryset(), slug=slug)


class AnnouncementListCreateView(AnnouncementBaseAPIView):
    def get(self, request):
        queryset = self.get_queryset()
        serializer = AnnouncementSerializer(queryset, many=True)
        return build_response(True, 200, "Announcements retrieved successfully.", serializer.data)

    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        if not serializer.is_valid():
            return build_response(False, 400, "Validation failed.", serializer.errors)

        user = request.user
        course = serializer.validated_data.get('course')

        if user.role == 'instructor':
            if not course or course.instructor.user != user:
                return build_response(False, 403, "You can only post announcements for your own courses.", None)

        serializer.save(instructor=user)
        return build_response(True, 201, "Announcement posted successfully.", serializer.data)


class AnnouncementDetailView(AnnouncementBaseAPIView):
    def get(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance)
        return build_response(True, 200, "Announcement retrieved successfully.", serializer.data)

    def patch(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return build_response(False, 400, "Validation failed.", serializer.errors)

        serializer.save()
        return build_response(True, 200, "Announcement updated successfully.", serializer.data)

    def put(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance, data=request.data)
        if not serializer.is_valid():
            return build_response(False, 400, "Validation failed.", serializer.errors)

        serializer.save()
        return build_response(True, 200, "Announcement updated successfully.", serializer.data)

    def delete(self, request, slug):
        instance = self.get_object(slug)
        instance.delete()
        return build_response(True, 200, "Announcement deleted successfully.", None)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request):
        queryset = self.get_queryset()
        serializer = NotificationSerializer(queryset, many=True)
        return build_response(
            True,
            200,
            "Notifications retrieved successfully.",
            {
                "unread_count": queryset.filter(is_read=False).count(),
                "notifications": serializer.data
            }
        )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        instance = get_object_or_404(Notification, user=request.user, slug=slug)
        serializer = NotificationSerializer(instance)
        return build_response(True, 200, "Notification retrieved successfully.", serializer.data)


class NotificationMarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=no_body, operation_description="Mark a specific notification as read. No request body required.")
    def post(self, request, slug):
        notification = get_object_or_404(Notification, user=request.user, slug=slug)
        notification.mark_as_read()
        return build_response(True, 200, "Notification marked as read.", None)


class NotificationMarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=no_body, operation_description="Mark all unread notifications as read at once. No request body required.")
    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return build_response(True, 200, f"{updated} notification(s) marked as read.", None)
