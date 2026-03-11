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
    ViewSet for handling Announcements.
    Instructors can create announcements for their assigned courses using course slugs.
    Admins can view and manage all announcements.
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Filter announcements based on user role.
        Admins see everything, instructors see only their own.
        """
        user = self.request.user
        # Optimizing query with select_related for performance
        queryset = Announcement.objects.select_related('instructor', 'course')
        
        if user.role == 'admin':
            return queryset.all()
        return queryset.filter(instructor=user)

    def create(self, request, *args, **kwargs):
        """
        Create a new announcement and validate instructor ownership of the course.
        The course is identified by its slug via the serializer.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"message": "Validation failed", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        # The serializer returns the actual Course object due to SlugRelatedField
        course = serializer.validated_data.get('course')

        # Instructor-specific authorization logic
        if user.role == 'instructor':
            # Check if the course belongs to the instructor's package
            if not course or course.package.instructor != user:
                return Response(
                    {"message": "Access Denied: You can only announce to your own courses."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Automatically assign the current user as the instructor/sender
        serializer.save(instructor=user)

        return Response(
            {
                "message": "Announcement sent successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        """
        List announcements filtered by the current user's permissions.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "message": "Announcements retrieved successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single announcement details by slug.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {
                "message": "Announcement retrieved successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


# =================== Notification ViewSet ===================
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for users to view and manage their personal notifications.
    Includes actions to mark single or all notifications as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def get_queryset(self):
        """
        Return only notifications belonging to the authenticated user.
        """
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Retrieve notifications list with an unread count for UI badges.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "message": "Notifications retrieved successfully",
                "data": {
                    "unread_count": queryset.filter(is_read=False).count(),
                    "notifications": serializer.data
                }
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, slug=None):
        """
        Custom action to mark a specific notification as read.
        """
        notification = self.get_object()
        notification.mark_as_read()
        return Response(
            {"message": "Notification marked as read"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_as_read(self, request):
        """
        Custom action to mark all unread notifications as read at once.
        """
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(
            {"message": "All notifications marked as read"},
            status=status.HTTP_200_OK
        )