from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Announcement, Notification
from .serializers import AnnouncementSerializer, NotificationSerializer
from users.permissions import IsInstructorOrAdmin


# =================== Announcement ViewSet ===================
class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    Instructors can create/manage announcements for their own courses.
    Admins can view and manage all announcements.
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related('instructor', 'course')
        if user.role == 'admin':
            return queryset.all()
        return queryset.filter(instructor=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "message": "Validation failed.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        course = serializer.validated_data.get('course')

        if user.role == 'instructor':
            # Course.instructor → FK to Instructor → .user → User
            if not course or course.instructor.user != user:
                return Response(
                    {
                        "status": "error",
                        "message": "You can only post announcements for your own courses.",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer.save(instructor=user)
        return Response(
            {
                "status": "success",
                "message": "Announcement posted successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "status": "success",
                "message": "Announcements retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "status": "success",
                "message": "Announcement retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "message": "Validation failed.",
                    "data": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response(
            {
                "status": "success",
                "message": "Announcement updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {
                "status": "success",
                "message": "Announcement deleted successfully.",
                "data": None
            },
            status=status.HTTP_200_OK
        )


# =================== Notification ViewSet ===================
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Users can view their own notifications and mark them as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "status": "success",
                "message": "Notifications retrieved successfully.",
                "data": {
                    "unread_count": queryset.filter(is_read=False).count(),
                    "notifications": serializer.data
                }
            },
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "status": "success",
                "message": "Notification retrieved successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, slug=None):
        """Mark a specific notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(
            {
                "status": "success",
                "message": "Notification marked as read.",
                "data": None
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_as_read(self, request):
        """Mark all unread notifications as read at once."""
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(
            {
                "status": "success",
                "message": f"{updated} notification(s) marked as read.",
                "data": None
            },
            status=status.HTTP_200_OK
        )