from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsAdmin
from users.serializers import InstructorCreateSerializer, InstructorSerializer, InstructorUpdateSerializer

# ===================== List All Instructors =====================
class InstructorListView(APIView):
    # permission_classes = [IsAdmin]

    @swagger_auto_schema(responses={200: InstructorSerializer(many=True)})
    def get(self, request):
        instructors = Instructor.objects.select_related("user").all()
        serializer = InstructorSerializer(instructors, many=True)
        return Response(
            {"message": "Instructors retrieved successfully", "data": serializer.data},
            status=status.HTTP_200_OK
        )

# ===================== Instructor Detail =====================
class InstructorDetailView(APIView):
    permission_classes = [IsInstructorOrAdmin]

    def get_object(self, slug):
        return Instructor.objects.select_related("user").filter(user__slug=slug).first()

    @swagger_auto_schema(responses={200: InstructorSerializer})
    def get(self, request, slug):
        instructor = self.get_object(slug)
        if not instructor:
            return Response({"message": "Instructor not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, instructor)
        serializer = InstructorSerializer(instructor)
        return Response({"message": "Instructor retrieved successfully", "data": serializer.data},
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=InstructorUpdateSerializer, responses={200: InstructorSerializer})
    def put(self, request, slug):
        instructor = self.get_object(slug)
        if not instructor:
            return Response({"message": "Instructor not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, instructor)
        serializer = InstructorUpdateSerializer(instructor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Instructor updated successfully", "data": serializer.data},
                        status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={204: "Instructor deleted successfully"})
    def delete(self, request, slug):
        instructor = self.get_object(slug)
        if not instructor:
            return Response({"message": "Instructor not found"}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, instructor)
        instructor.delete()
        return Response({"message": "Instructor deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# ===================== Create Instructor =====================
class InstructorCreateView(APIView):
    permission_classes = [IsAdmin]
    @swagger_auto_schema(request_body=InstructorCreateSerializer, responses={201: InstructorSerializer})
    def post(self, request):
        serializer = InstructorCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instructor = serializer.save()
        return Response(
            {
                "message": "Instructor created successfully",
                "instructor_email": instructor.user.email,
                "instructor_name": f"{instructor.user.first_name} {instructor.user.last_name}"
            },
            status=status.HTTP_201_CREATED
        )