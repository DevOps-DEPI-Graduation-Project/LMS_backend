from django.apps import apps
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.http import Http404
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Value, BooleanField

from users.permissions import IsCourseOwnerOrAdmin, IsEnrolledOrAdminOrInstructorOwn, IsInstructorOrAdmin, IsVideoOwnerOrAdmin
from videos.models import Video
from videos.serializers import VideoSerializer, CourseVideosSerializer
from utils import apiResponse
from rest_framework.parsers import MultiPartParser, FormParser
from cources.models import Course

from videos.service import VideoService

success_response = apiResponse.success_response
error_response = apiResponse.error_response


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class to safely bound memory constraints during high-volume queries."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ======================== Get all videos =======================
class VideosListApiView(ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsInstructorOrAdmin]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        # Multitenancy scoping to prevent instructors from leaking other instructor assets
        if self.request.user.is_staff:
            return Video.objects.all().order_by('-created_at')
        return Video.objects.filter(course__instructor=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
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
            
        try:
            video = VideoService.create_or_update_video(video_slug=None, **serializer.validated_data)
            output_serializer = VideoSerializer(video)
            return success_response(
                message="Video created successfully and processing pipeline started.",
                data=output_serializer.data
            )
        except ValidationError as ve:
            return error_response(
                message="Validation failed inside the service layer.",
                errors={"validation": str(ve)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                message="An error occurred while deploying the video service.",
                errors={"server": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ======================= Delete video =========================
class VideosDestroyApiView(DestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsVideoOwnerOrAdmin]
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


# =========================== Update video ======================
class VideosUpdateApiView(UpdateAPIView):
    queryset = Video.objects.all() 
    serializer_class = VideoSerializer
    permission_classes = [IsVideoOwnerOrAdmin]
    lookup_field = 'slug'

    def update(self, request, *args, **kwargs):
        try:
            video = self.get_object()
        except NotFound:
            return error_response(
                message="Video not exist",
                status_code=status.HTTP_404_NOT_FOUND
            )
            
        serializer = VideoSerializer(video, data=request.data, partial=True)
        if not serializer.is_valid():
             return error_response(
                message="Invalid video data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
             
        try:
            updated_video = VideoService.create_or_update_video(video_slug=video.slug, **serializer.validated_data)
        except Http404 as e:
            return error_response(message=str(e), status_code=status.HTTP_404_NOT_FOUND)
        
        output_serializer = VideoSerializer(updated_video)
        return success_response(
            message="Video updated successfully.",
            data=output_serializer.data
        )
        

# ============================= Videos in Course ==============================
class CourseVideosListApiView(ListAPIView):
    serializer_class = CourseVideosSerializer
    permission_classes = [IsEnrolledOrAdminOrInstructorOwn]
    
    def get_queryset(self):
        course_slug = self.kwargs.get("course_slug")
        student = getattr(self.request.user, 'student_profile', None)

        # Uses database-level joins via select_related to optimize context data extraction
        queryset = Video.objects.select_related("course").filter(
            course__slug=course_slug
        ).order_by("order")

        # Computes completion matrices on the database layer to completely resolve N+1 overhead query bugs
        if student:
            is_completed_subquery = apps.get_model('videos', 'VideoProgress').objects.filter(
                video=OuterRef('pk'),
                student=student,
                is_completed=True
            )
            queryset = queryset.annotate(is_completed=Exists(is_completed_subquery))
        else:
            queryset = queryset.annotate(is_completed=Value(False, output_field=BooleanField()))

        return queryset

    def list(self, request, *args, **kwargs):
        course_slug = self.kwargs.get("course_slug")
        course = Course.objects.filter(slug=course_slug).first()

        if not course:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Unified single direct query hit execution mapping
        videos = self.get_queryset()
        serializer = self.get_serializer(videos, many=True)
        return success_response(
            message="Videos retrieved successfully",
            data=serializer.data
        )