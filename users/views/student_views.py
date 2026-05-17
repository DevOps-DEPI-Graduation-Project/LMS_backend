from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from users.models import Student
from users.permissions import IsAdmin, IsStudentOrAdmin
from users.serializers import (
    StudentSerializer,
    StudentUpdateSerializer
)
from users.permissions import IsAdmin

from utils.apiResponse import success_response, error_response


#======================all student=======================
class StudentListView(APIView):
    permission_classes = [IsAdmin]

    @swagger_auto_schema(responses={200: StudentSerializer(many=True)})
    def get(self, request):
        students = Student.objects.select_related("user").all()
        serializer = StudentSerializer(students, many=True)

        return success_response(
            message="Students retrieved successfully",
            data=serializer.data
        )

#================= Student Profile / Update / Delete==========================
 
class StudentDetailView(APIView):
    permission_classes = [IsStudentOrAdmin]

    def get_object(self, slug):
        return Student.objects.select_related("user").filter(user__slug=slug).first()
    @swagger_auto_schema(responses={200: StudentSerializer})
    def get(self, request, slug):

        student = self.get_object(slug)

        if not student:
            return error_response(
                message="Student not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, student)

        serializer = StudentSerializer(student)

        return success_response(
            message="Student retrieved successfully",
            data=serializer.data
        )

    @swagger_auto_schema(
        request_body=StudentUpdateSerializer,
        responses={200: StudentSerializer}
    )
    def put(self, request, slug):

        student = self.get_object(slug)

        if not student:
            return error_response(
                message="Student not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, student)

        serializer = StudentUpdateSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return success_response(
                message="Student updated successfully",
                data=serializer.data
            )

        return error_response(
            message="Invalid data",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(responses={204: "Student deleted successfully"})
    def delete(self, request, slug):

        student = self.get_object(slug)

        if not student:
            return error_response(
                message="Student not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, student)

        student.delete()

        return success_response(
            message="Student deleted successfully",
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )