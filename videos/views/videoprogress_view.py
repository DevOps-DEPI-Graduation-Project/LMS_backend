from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from videos.models import Video, VideoProgress
from videos.serializers import VideoProgressSerializer
from utils.apiResponse import success_response, error_response


from datetime import timedelta

class VideoCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_slug):
        student = request.user.student_profile
        current_time = float(request.data.get("current_time", 0))
        duration = request.data.get("duration", None)

        video = Video.objects.filter(slug=video_slug).first()
        if not video:
            return error_response(
                "Video not found",
                status.HTTP_404_NOT_FOUND
            )

        if duration and not video.duration:
            video.duration = timedelta(seconds=float(duration))
            video.save()

        progress, _ = VideoProgress.objects.get_or_create(
            student=student,
            video=video
        )

        progress.update_progress(current_time)

        return success_response(
            "Progress updated",
            VideoProgressSerializer(progress).data,
            status.HTTP_200_OK
        )