from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView,UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Video
from .serializers import VideoSerializer
from utils import apiResponse

success_response = apiResponse.success_response
error_response = apiResponse.error_response

# ======================== Get all videos =======================
class VideosListApiView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        videos = self.get_queryset()
        if not videos.exists():
            return success_response(
                message="No videos available",
                data=[]
            )
        serializer = VideoSerializer(videos, many=True)
        return success_response(
            message="Videos retrieved successfully",
            data=serializer.data
        )

# ======================= Create video =========================
class VideosCreateApiView(CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = VideoSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid video data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return success_response(
            message="Video created successfully",
            data=serializer.data
        )

# ======================= Delete video =========================
class VideosDestroyApiView(DestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def destroy(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except Exception:
            return success_response(
                message="Video not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        video.delete()
        return success_response(
            message="Video deleted successfully",
            data=None
        )

# ======================= Retrieve video =======================
class VideosRetrieveApiView(RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except Exception:
            return success_response(
                message="Video not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = VideoSerializer(video)
        return success_response(
            message="Video retrieved successfully",
            data=serializer.data
        )
    #===========================update video======================
class VideosUpdateApiView(UpdateAPIView):
    queryset = Video.objects.all() 
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except Exception:
            return success_response(
                message="Video not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = VideoSerializer(video,data=request.data,partial=True)

        if not serializer.is_valid():
             return error_response(
                message="Invalid video data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return success_response(
            message="Video updated successfully",
            data=serializer.data
        )