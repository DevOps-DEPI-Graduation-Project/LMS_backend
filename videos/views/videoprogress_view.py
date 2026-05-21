from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from videos.models import Video, VideoProgress
from utils.apiResponse import success_response, error_response
from videos.serializers import VideoProgressSerializer
class VideoCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_slug):
        student = request.user.student_profile

        video = Video.objects.filter(slug=video_slug).first()

        if not video:
            return error_response(
                "Video not found",
                status.HTTP_404_NOT_FOUND
            )

        progress, _ = VideoProgress.objects.get_or_create(
            student=student,
            video=video
        )

        progress.is_completed = True
        progress.save()

        return success_response(
            "Video completed successfully",
            VideoProgressSerializer(progress).data,
            status.HTTP_200_OK
        )