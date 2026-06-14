from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
# Assuming Enrollment model lives inside cources.models or a similar module
from cources.models import Course 
# Adjust this import to match your actual enrollment app model location (e.g., enrollments.models)
from django.apps import apps

from videos.models import Video, VideoProgress
from utils.apiResponse import success_response, error_response
from videos.serializers import VideoProgressSerializer

class VideoCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_slug):
        student = request.user.student_profile

        video = Video.objects.filter(slug=video_slug).select_related('course').first()
        if not video:
            return error_response("Video not found", status.HTTP_404_NOT_FOUND)
            
        if not video.is_ready:
            return error_response("Video is not ready or has missing duration tracking metrics.", status.HTTP_400_BAD_REQUEST)

        # FIX 3: Strict Security Access Control Layer.
        # Dynamically checks if the active student profile has a valid active Enrollment in the parent course.
        Enrollment = apps.get_model('enrollments', 'Enrollment') # Update 'enrollments' app name if different
        is_enrolled = Enrollment.objects.filter(student=student, course=video.course, is_active=True).exists()
        
        # Bypass check if the user is a staff member or the specific course instructor
        is_privileged = request.user.is_staff or (video.course.instructor == request.user)
        
        if not is_enrolled and not is_privileged:
            return error_response(
                "Access Denied. You must be enrolled in this course to track progress.", 
                status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            progress, created = VideoProgress.objects.get_or_create(student=student, video=video)
            if not created:
                progress = VideoProgress.objects.select_for_update().get(pk=progress.pk)

            progress.mark_completed()

        serializer = VideoProgressSerializer(progress)
        return success_response(
            message="Video progress marked as completed successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )