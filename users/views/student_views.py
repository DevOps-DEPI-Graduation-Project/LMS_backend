
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import User,Student
from users.permissions import IsAdmin, IsStudent
from users.serializers import StudentSerializer, StudentUpdateSerializer, StudentUpdateSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
#=====================all students=========================
class StudentListView(APIView):
    permission_classes = [IsAdmin]
    @swagger_auto_schema(responses={200: StudentSerializer(many=True)})
    def get(self, request):
        students = Student.objects.select_related("user").all()
        serializer = StudentSerializer(students, many=True)
        return Response(
            {
                "message": "Students retrieved successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


# ================= update/ delete/ profile student =================
class StudentDetailView(APIView):
    permission_classes = [IsAdmin, IsStudent]
    def get_object(self, slug):
        return Student.objects.select_related("user").filter(user__slug=slug).first()
## student profile
    @swagger_auto_schema(responses={200: StudentSerializer})
    def get(self, request, slug):
        student = self.get_object(slug)
        if not student:
            return Response(
                {"message": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, student)
        
        serializer = StudentSerializer(student)
        return Response(
            {"message": "Student retrieved successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )
    @swagger_auto_schema(request_body=StudentUpdateSerializer, responses={200: StudentSerializer})
    def put(self, request, slug):
        student = self.get_object(slug)
        if not student:
            return Response(
                {"message": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, student)
        serializer = StudentUpdateSerializer(student, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Student updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(responses={204: "Student deleted successfully"})
    def delete(self, request, slug):
        student = self.get_object(slug)
        if not student:
            return Response(
                {"message": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, student)
        student.delete()
        return Response(
            {"message": "Student deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )