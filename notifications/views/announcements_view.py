from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from notifications.models import Announcement
from notifications.serializers import AnnouncementSerializer
from users.permissions import IsInstructorOrAdmin
from utils.apiResponse import success_response, error_response
from utils.pagination import AnnouncementsPagination


class AnnouncementBaseAPIView(APIView):
    def get_permissions(self):
        if self.request.method in ['GET']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsInstructorOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        queryset = Announcement.objects.select_related('instructor', 'course')
        
        if user.role == 'admin':
            return queryset.all()
        
        if user.role == 'instructor':
            return queryset.filter(instructor=user)
            
        # For students: show announcements for courses they are enrolled in
        return queryset.filter(course__enrollments__student=user).distinct()

    def get_object(self, slug):
        return get_object_or_404(self.get_queryset(), slug=slug)


class AnnouncementListCreateView(AnnouncementBaseAPIView):
    def get(self, request):
        queryset = self.get_queryset()
        
        # Pagination
        paginator = AnnouncementsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            serializer = AnnouncementSerializer(queryset, many=True)
            return success_response("Announcements retrieved successfully.", serializer.data)
        
        serializer = AnnouncementSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(
            serializer.data,
            message="Announcements retrieved successfully."
        )

    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = request.user
        course = serializer.validated_data.get('course')

        if user.role == 'instructor':
            if not course or course.instructor.user != user:
                return error_response("You can only post announcements for your own courses.", None, status.HTTP_403_FORBIDDEN)

        serializer.save(instructor=user)
        return success_response("Announcement posted successfully.", serializer.data, status.HTTP_201_CREATED)


class AnnouncementDetailView(AnnouncementBaseAPIView):
    def get(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance)
        return success_response("Announcement retrieved successfully.", serializer.data)

    def patch(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response("Announcement updated successfully.", serializer.data)

    def put(self, request, slug):
        instance = self.get_object(slug)
        serializer = AnnouncementSerializer(instance, data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response("Announcement updated successfully.", serializer.data)

    def delete(self, request, slug):
        instance = self.get_object(slug)
        instance.delete()
        return success_response("Announcement deleted successfully.", None)
