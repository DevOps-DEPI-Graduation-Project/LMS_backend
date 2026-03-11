import os
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse

from .models import Material
from .serializer import MaterialSerializer
from users.permissions import IsInstructorOrAdmin


class MaterialViewSet(viewsets.ModelViewSet):
    """
    Final optimized ViewSet:
    - role-based access (admin, instructor, student)
    - full CRUD with consistent responses
    - instructor ownership check for create/update
    - secure file download
    """
    queryset = Material.objects.select_related("course").all()
    serializer_class = MaterialSerializer
    lookup_field = "slug"
    parser_classes = (MultiPartParser, FormParser)

    # filter_backends = [ filters.SearchFilter]
    # search_fields = ["Material_Name", "course__title", "course__slug"]
    # filterset_fields = ["course"]

    # ----- Role-based permissions -----
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsInstructorOrAdmin()]

    # ----- Filter queryset based on role -----
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.role == "admin":
            return queryset
        elif user.role == "instructor":
            return queryset.filter(course__package__instructor=user).distinct()
        elif user.role == "student":
            return queryset.filter(course__enrollment__student=user).distinct()
        return Material.objects.none()

    # ----- Helper: check instructor owns the course -----
    def _check_instructor_ownership(self, user, course):
        if user.role == "instructor" and course.package.instructor != user:
            return Response(
                {"message": "Unauthorized: You don't own this course"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    # ----- List -----
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Materials retrieved successfully" if queryset.exists() else "No materials available",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Create -----
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data["course"]
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return Response({
            "message": "Material created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    # ----- Retrieve -----
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Material retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Update -----
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            return Response({
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data.get("course", instance.course)
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return Response({
            "message": "Material updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Destroy -----
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Material deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)

    # ----- Download Action -----
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def download(self, request, slug=None):
        """
        Custom action to handle secure file downloads.
        URL: /api/materials/{slug}/download/
        """
        material = self.get_object()

        if not material.file:
            return Response(
                {"message": "No file attached to this material"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Optional: check ownership if instructor
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
            return Response(
                {"message": f"Error opening file: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MaterialViewSet(viewsets.ModelViewSet):
    """
    Final optimized ViewSet:
    - role-based access (admin, instructor, student)
    - full CRUD with consistent responses
    - instructor ownership check for create/update
    - secure file download
    """
    queryset = Material.objects.select_related("course").all()
    serializer_class = MaterialSerializer
    lookup_field = "slug"
    parser_classes = (MultiPartParser, FormParser)

    # filter_backends = [ filters.SearchFilter]
    # search_fields = ["Material_Name", "course__title", "course__slug"]
    # filterset_fields = ["course"]

    # ----- Role-based permissions -----
    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsInstructorOrAdmin()]

    # ----- Filter queryset based on role -----
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.role == "admin":
            return queryset
        elif user.role == "instructor":
            return queryset.filter(course__package__instructor=user).distinct()
        elif user.role == "student":
            return queryset.filter(course__enrollment__student=user).distinct()
        return Material.objects.none()

    # ----- Helper: check instructor owns the course -----
    def _check_instructor_ownership(self, user, course):
        if user.role == "instructor" and course.package.instructor != user:
            return Response(
                {"message": "Unauthorized: You don't own this course"},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    # ----- List -----
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Materials retrieved successfully" if queryset.exists() else "No materials available",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Create -----
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data["course"]
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return Response({
            "message": "Material created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    # ----- Retrieve -----
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "message": "Material retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Update -----
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if not serializer.is_valid():
            return Response({
                "message": "Validation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.validated_data.get("course", instance.course)
        check = self._check_instructor_ownership(request.user, course)
        if check:
            return check

        serializer.save()
        return Response({
            "message": "Material updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ----- Destroy -----
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Material deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)

    # ----- Download Action -----
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def download(self, request, slug=None):
        """
        Custom action to handle secure file downloads.
        URL: /api/materials/{slug}/download/
        """
        material = self.get_object()

        if not material.file:
            return Response(
                {"message": "No file attached to this material"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Optional: check ownership if instructor
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
            return Response(
                {"message": f"Error opening file: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )