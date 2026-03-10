from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Announcement, Notification
from .services import get_target_users, create_announcement_notifications
from .serializers import AnnouncementSerializer, NotificationSerializer


# =================== Allowed target types per role ===================
INSTRUCTOR_ALLOWED_TARGETS = {'course_students', 'all_students'}
ADMIN_ALLOWED_TARGETS = {'all_users', 'all_students', 'all_instructors', 'course_students', 'specific_users'}


# =================== Create Announcement ===================
class AnnouncementCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        target_type = request.data.get('target_type')

        # Role check
        if user.role == 'student':
            return Response(
                {"detail": "Students are not allowed to send announcements."},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'instructor' and target_type not in INSTRUCTOR_ALLOWED_TARGETS:
            return Response(
                {"detail": f"Instructors can only send to: {', '.join(INSTRUCTOR_ALLOWED_TARGETS)}."},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'admin' and target_type not in ADMIN_ALLOWED_TARGETS:
            return Response(
                {"detail": f"Invalid target type."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AnnouncementSerializer(data=request.data)
        if serializer.is_valid():
            announcement = serializer.save(sender=user)
            users = get_target_users(announcement)
            create_announcement_notifications(announcement, users)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =================== List Notifications ===================
class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


# =================== Mark Notification as Read ===================
class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return Response({"detail": "Notification marked as read."}, status=status.HTTP_200_OK)