from rest_framework.generics import ListAPIView,CreateAPIView,RetrieveAPIView,DestroyAPIView,UpdateAPIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
import math
from users.models import Instructor, InstructorLinks
from users.permissions import IsInstructorOrAdmin, IsAdmin
from users.serializers import (
    InstructorCreateSerializer,
    InstructorSerializer,
    InstructorUpdateSerializer,
)

from utils.apiResponse import success_response, error_response
from django.db import transaction
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

# ---------------- Pagination Class ---------------- 
class InstructorPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 50

# ---------------- List All Instructors API ----------------
class InstructorListAPIView(ListAPIView):
    queryset = Instructor.objects.select_related("user").order_by('-id')
    serializer_class = InstructorSerializer
    permission_classes =[IsAdmin]
    pagination_class = InstructorPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return success_response(
                message="No instructors available",
                data={
                    "total_instructors": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "instructors": []
                }
            )

        #  paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Instructors retrieved successfully",
            data={
                "total_instructors": len(serializer.data),
                "total_pages": 1,
                "current_page": 1,
                "instructors": serializer.data
            }
        )

    # ---------------- Paginated Response ----------------
    def get_paginated_response(self, data):
        return success_response(
            message="Instructors retrieved successfully",
            data={
                "total_instructors": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "instructors": data
            }
        )
        
#==================================profile===================================
class InstructorDetailView(RetrieveAPIView):
    queryset = Instructor.objects.select_related("user").all()
    serializer_class = InstructorSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_object(self):
        slug = self.kwargs.get("slug")
        instructor = self.queryset.filter(user__slug=slug).first()
        if not instructor:
            return None
        self.check_object_permissions(self.request, instructor)
        return instructor

    def retrieve(self, request, *args, **kwargs):
        instructor = self.get_object()
        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=404
            )

        serializer = self.get_serializer(instructor)
        return success_response(
            message="Instructor retrieved successfully",
            data=serializer.data
        )
        
#===========================================update========================================
class InstructorUpdateView(UpdateAPIView):
    queryset = Instructor.objects.select_related("user").all()
    serializer_class = InstructorUpdateSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_object(self):
        slug = self.kwargs.get("slug")
        instructor = self.queryset.filter(user__slug=slug).first()
        if not instructor:
            return None
        self.check_object_permissions(self.request, instructor)
        return instructor

    def update(self, request, *args, **kwargs):
        instructor = self.get_object()
        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=404
            )

        serializer = self.get_serializer(
            instructor,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(
            message="Instructor updated successfully",
            data=serializer.data
        )
        
#======================================delete========================================
class InstructorDeleteView(DestroyAPIView):
    queryset = Instructor.objects.select_related("user").all()
    permission_classes = [IsInstructorOrAdmin]

    def get_object(self):
        slug = self.kwargs.get("slug")
        instructor = self.queryset.filter(user__slug=slug).first()
        if not instructor:
            return None
        self.check_object_permissions(self.request, instructor)
        return instructor

    def destroy(self, request, *args, **kwargs):
        instructor = self.get_object()
        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=404
            )
        user = instructor.user
        with transaction.atomic():
            user.delete()
            
        return success_response(
            message="Instructor deleted successfully",
            data=None,
            status_code=204
        )
##============================create instructor=========================
class InstructorCreateView(CreateAPIView):
    serializer_class = InstructorCreateSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instructor = serializer.save()

        return success_response(
            message="Instructor created successfully",
            data={
                "instructor_email": instructor.user.email,
                "instructor_name": f"{instructor.user.first_name} {instructor.user.last_name}"
            },
            status_code=201
        )