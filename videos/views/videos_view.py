from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView,UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework import status
from users.permissions import IsCourseOwnerOrAdmin, IsEnrolledOrAdminOrInstructorOwn, IsInstructorOrAdmin
from  videos.models import Video
from videos.serializers import VideoSerializer,CourseVideosSerializer
from utils import apiResponse
from cources.models import  Course, Enrollment
success_response = apiResponse.success_response
error_response = apiResponse.error_response
# ======================== Get all videos =======================
class VideosListApiView(ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsInstructorOrAdmin]

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
    permission_classes = [IsInstructorOrAdmin]
    
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
    permission_classes = [IsCourseOwnerOrAdmin]
    lookup_field = 'slug'

    def destroy(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except NotFound:
            return error_response(
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
    permission_classes = [IsEnrolledOrAdminOrInstructorOwn]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except NotFound:
            return error_response(
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
    permission_classes = [IsCourseOwnerOrAdmin]
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except NotFound:
            return error_response(
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
        
#=============================videos in course==============================

class CourseVideosListApiView(ListAPIView):
    serializer_class = CourseVideosSerializer
    permission_classes = [IsEnrolledOrAdminOrInstructorOwn]
    
    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")

        return Video.objects.select_related("course").filter(
            course__slug=course_slug
        ).order_by("order")
    

    def list(self, request, *args, **kwargs):
        
        course_slug = self.kwargs.get("course_slug")
        course=Course.objects.filter(slug=course_slug).first()

        if not course:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        videos = self.get_queryset()

        if not videos.exists():
            return success_response(
                message="No videos available for this course",
                data=[]
            )

        serializer = self.get_serializer(videos, many=True)

        return success_response(
            message="Videos retrieved successfully",
            data=serializer.data
        )