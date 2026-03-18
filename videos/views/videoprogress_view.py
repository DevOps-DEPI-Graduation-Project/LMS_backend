from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from  videos.models import VideoProgress,Video
from videos.serializers import VideoProgressSerializer
from utils.apiResponse import success_response,error_response


class VideoCompleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, video_slug):
        user = request.user

        try:
            video = Video.objects.get(slug=video_slug)
        except Video.DoesNotExist:
            return error_response({
                "status": False,
                "message": "Video not found",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        progress, created = VideoProgress.objects.get_or_create(
            user=user,
            video=video,
            defaults={"is_completed": True}  )

        if not created and not progress.is_completed:
            progress.is_completed = True
            progress.save()

        serializer = VideoProgressSerializer(progress)
        return success_response({
            "status": True,
            "message": "Video marked as completed",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
        
