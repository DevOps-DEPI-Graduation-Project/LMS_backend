from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from users.models import Instructor, InstructorLinks
from users.permissions import IsInstructorOrAdmin, IsAdmin
from users.serializers import (
    InstructorCreateSerializer,
    InstructorSerializer,
    InstructorUpdateSerializer,
    InstructorLinksSerializer
)

from utils.apiResponse import success_response, error_response


# ===================== all instructors =====================
class InstructorListView(APIView):
    # permission_classes = [IsAdmin]

    @swagger_auto_schema(responses={200: InstructorSerializer(many=True)})
    def get(self, request):
        instructors = Instructor.objects.select_related("user").all()
        serializer = InstructorSerializer(instructors, many=True)

        return success_response(
            message="Instructors retrieved successfully",
            data=serializer.data
        )


# ===================== instructor detail =====================
class InstructorDetailView(APIView):
    permission_classes = [IsInstructorOrAdmin]

    def get_object(self, slug):
        return Instructor.objects.select_related("user").filter(user__slug=slug).first()

    @swagger_auto_schema(responses={200: InstructorSerializer})
    def get(self, request, slug):

        instructor = self.get_object(slug)

        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, instructor)

        serializer = InstructorSerializer(instructor)

        return success_response(
            message="Instructor retrieved successfully",
            data=serializer.data
        )

    @swagger_auto_schema(
        request_body=InstructorUpdateSerializer,
        responses={200: InstructorSerializer}
    )
    def put(self, request, slug):

        instructor = self.get_object(slug)

        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, instructor)

        serializer = InstructorUpdateSerializer(
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

    @swagger_auto_schema(responses={204: "Instructor deleted successfully"})
    def delete(self, request, slug):

        instructor = self.get_object(slug)

        if not instructor:
            return error_response(
                message="Instructor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, instructor)

        instructor.delete()

        return success_response(
            message="Instructor deleted successfully",
            data=None,
            status_code=status.HTTP_204_NO_CONTENT
        )


# ===================== Create Instructor =====================
class InstructorCreateView(APIView):
    # permission_classes = [IsAdmin]

    @swagger_auto_schema(
        request_body=InstructorCreateSerializer,
        responses={201: InstructorSerializer}
    )
    def post(self, request):

        serializer = InstructorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instructor = serializer.save()

        return success_response(
            message="Instructor created successfully",
            data={
                "instructor_email": instructor.user.email,
                "instructor_name": f"{instructor.user.first_name} {instructor.user.last_name}"
            },
            status_code=status.HTTP_201_CREATED
        )