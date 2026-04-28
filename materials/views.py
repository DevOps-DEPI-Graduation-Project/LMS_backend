import os
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.http import FileResponse

from .models import Material
from .serializer import MaterialSerializer
from users.permissions import IsInstructorOrAdmin
from utils.apiResponse import success_response, error_response
from utils.pagination import MaterialsPagination


class MaterialBaseAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsInstructorOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        queryset = Material.objects.select_related("course").all()

        if user.role == "admin":
            return queryset
        elif user.role == "instructor":
            return queryset.filter(course__instructor__user=user).distinct()
        elif user.role == "student":
            return queryset.filter(course__enrollments__student=user).distinct()
        return Material.objects.none()

    def get_object(self, slug):
        return get_object_or_404(self.get_queryset(), slug=slug)

    def _check_instructor_ownership(self, user, course):
        if user.role == "instructor" and course.instructor.user != user:
            return error_response(
                "Unauthorized: You don't own this course",
                None,
                status.HTTP_403_FORBIDDEN
            )
        return None


class MaterialListCreateView(MaterialBaseAPIView):
    def get(self, request):
        queryset = self.get_queryset()
        
        # Pagination
        paginator = MaterialsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            serializer = MaterialSerializer(queryset, many=True, context={"request":request})
            return success_response(
                "Materials retrieved successfully" if queryset.exists() else "No materials available",
                serializer.data
            )
        
        serializer = MaterialSerializer(paginated_queryset, many=True,  context={"request":request})
        return paginator.get_paginated_response(
            serializer.data,
            message="Materials retrieved successfully."
        )

    def post(self, request):
        serializer = MaterialSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data["course"]
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return success_response("Material created successfully", serializer.data, status.HTTP_201_CREATED)


class MaterialDetailView(MaterialBaseAPIView):
    def get(self, request, slug):
        instance = self.get_object(slug)
        serializer = MaterialSerializer(instance, context={"request": request})
        return success_response("Material retrieved successfully", serializer.data)

    def patch(self, request, slug):
        instance = self.get_object(slug)
        serializer = MaterialSerializer(instance, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data.get("course", instance.course)
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return success_response("Material updated successfully", serializer.data)

    def put(self, request, slug):
        instance = self.get_object(slug)
        serializer = MaterialSerializer(instance, data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data.get("course", instance.course)
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return success_response("Material updated successfully", serializer.data)

    def delete(self, request, slug):
        instance = self.get_object(slug)
        instance.delete()
        return success_response("Material deleted successfully", None)


class MaterialDownloadView(MaterialBaseAPIView):
    def get(self, request, slug):
        material = self.get_object(slug)

        if not material.file:
            return error_response("No file attached to this material", None, status.HTTP_404_NOT_FOUND)

        check = self._check_instructor_ownership(request.user, material.course)
        if check:
            return check

        try:
            return FileResponse(
                material.file.open('rb'),
                as_attachment=True,
                filename=os.path.basename(material.file.name)
            )
        except Exception as e:
            return error_response(f"Error opening file: {str(e)}", None, status.HTTP_500_INTERNAL_SERVER_ERROR)
