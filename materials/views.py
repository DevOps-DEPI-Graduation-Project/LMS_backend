import os
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from django.http import FileResponse
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Material
from .serializer import MaterialSerializer, CourseMaterialCreateSerializer
from cources.models import Course
from users.permissions import IsInstructorOrAdmin
from utils.apiResponse import success_response, error_response
from utils.pagination import MaterialsPagination


class CourseMaterialListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @swagger_auto_schema(
        operation_description="List all materials for the specified course",
        responses={200: MaterialSerializer(many=True)},
        tags=['Materials']
    )
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            if not course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", None, status.HTTP_403_FORBIDDEN)

        queryset = Material.objects.filter(course=course).order_by('-created_at')

        # Pagination
        paginator = MaterialsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        if paginated_queryset is None:
            serializer = MaterialSerializer(queryset, many=True, context={"request": request})
            return success_response(
                "Course materials retrieved successfully" if queryset.exists() else "No materials available for this course",
                serializer.data
            )

        serializer = MaterialSerializer(paginated_queryset, many=True, context={"request": request})
        return paginator.get_paginated_response(
            serializer.data,
            message="Course materials retrieved successfully."
        )

    @swagger_auto_schema(
        operation_description="Create a new material for the specified course",
        manual_parameters=[
            openapi.Parameter('Material_Name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ],
        responses={201: MaterialSerializer, 400: "Bad Request"},
        tags=['Materials'],
        consumes=['multipart/form-data']
    )
    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can create materials.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only add materials to your own course.", None, status.HTTP_403_FORBIDDEN)

        serializer = CourseMaterialCreateSerializer(
            data=request.data, 
            context={"request": request}
        )
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save(course=course)
        return success_response("Material created successfully", serializer.data, status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Update a material for the specified course",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Slug of material to update"),
            openapi.Parameter('Material_Name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        responses={200: MaterialSerializer, 400: "Bad Request"},
        tags=['Materials'],
        consumes=['multipart/form-data']
    )
    def patch(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can update materials.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only update materials for your own course.", None, status.HTTP_403_FORBIDDEN)

        material_slug = request.data.get('slug') or request.data.get('material_slug')
        if not material_slug:
            return error_response("Material slug is required for update.", None, status.HTTP_400_BAD_REQUEST)

        material = get_object_or_404(Material, slug=material_slug, course=course)

        serializer = CourseMaterialCreateSerializer(
            instance=material,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response("Material updated successfully", serializer.data)

    @swagger_auto_schema(
        operation_description="Delete a material from the specified course",
        manual_parameters=[
            openapi.Parameter('slug', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Slug of material to delete"),
        ],
        responses={200: "Deleted", 403: "Forbidden", 404: "Not Found"},
        tags=['Materials'],
        consumes=['multipart/form-data', 'application/json']
    )
    def delete(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can delete materials.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only delete materials from your own course.", None, status.HTTP_403_FORBIDDEN)

        material_slug = request.data.get('slug') or request.data.get('material_slug')
        if not material_slug:
            return error_response("Material slug is required for delete.", None, status.HTTP_400_BAD_REQUEST)

        material = get_object_or_404(Material, slug=material_slug, course=course)
        material.delete()
        return success_response("Material deleted successfully", None)


class MaterialBaseAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser, JSONParser)

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
    @swagger_auto_schema(
        operation_description="List all materials",
        responses={200: MaterialSerializer(many=True)},
        tags=['Materials']
    )
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

    @swagger_auto_schema(
        operation_description="Create a new material",
        manual_parameters=[
            openapi.Parameter('course', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description="Course slug"),
            openapi.Parameter('Material_Name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ],
        responses={201: MaterialSerializer, 400: "Bad Request"},
        tags=['Materials'],
        consumes=['multipart/form-data']
    )
    def post(self, request):
        serializer = MaterialSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data["course"]
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return success_response("Material created successfully", serializer.data, status.HTTP_201_CREATED)


class MaterialDetailView(MaterialBaseAPIView):
    @swagger_auto_schema(
        operation_description="Get material details",
        responses={200: MaterialSerializer, 404: "Not Found"},
        tags=['Materials']
    )
    def get(self, request, slug):
        instance = self.get_object(slug)
        serializer = MaterialSerializer(instance, context={"request": request})
        return success_response("Material retrieved successfully", serializer.data)

    @swagger_auto_schema(
        operation_description="Partially update a material",
        manual_parameters=[
            openapi.Parameter('Material_Name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        responses={200: MaterialSerializer, 400: "Bad Request"},
        tags=['Materials'],
        consumes=['multipart/form-data']
    )
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

    @swagger_auto_schema(
        operation_description="Update a material",
        manual_parameters=[
            openapi.Parameter('course', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('Material_Name', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ],
        responses={200: MaterialSerializer, 400: "Bad Request"},
        tags=['Materials'],
        consumes=['multipart/form-data']
    )
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

    @swagger_auto_schema(
        operation_description="Delete a material",
        responses={200: "Deleted", 404: "Not Found"},
        tags=['Materials']
    )
    def delete(self, request, slug):
        instance = self.get_object(slug)
        instance.delete()
        return success_response("Material deleted successfully", None)


class MaterialDownloadView(MaterialBaseAPIView):
    @swagger_auto_schema(
        operation_description="Download a material file",
        responses={200: "File output", 404: "Not Found"},
        tags=['Materials']
    )
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