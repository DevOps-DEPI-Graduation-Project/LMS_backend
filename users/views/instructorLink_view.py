from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Instructor, InstructorLinks
from users.permissions import IsInstructorOrAdmin
from users.serializers import InstructorLinksSerializer


# ===================== Instructor Links Management =====================

class InstructorLinksListView(ListAPIView):
    serializer_class = InstructorLinksSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')
        try:
            instructor = Instructor.objects.get(user__slug=instructor_slug)
            return InstructorLinks.objects.filter(instructor=instructor)
        except Instructor.DoesNotExist:
            return InstructorLinks.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"message": "No links found"}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response({"message": "Links retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)


class InstructorLinksCreateView(CreateAPIView):
    serializer_class = InstructorLinksSerializer
    permission_classes = [IsInstructorOrAdmin]

    def create(self, request, *args, **kwargs):
        instructor_slug = self.kwargs.get('instructor_slug')
        try:
            instructor = Instructor.objects.get(user__slug=instructor_slug)
        except Instructor.DoesNotExist:
            return Response({"message": "Instructor not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.instructor_profile != instructor:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(instructor=instructor)
            return Response({"message": "Link created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InstructorLinksUpdateView(UpdateAPIView):
    queryset = InstructorLinks.objects.all()
    serializer_class = InstructorLinksSerializer
    permission_classes = [IsInstructorOrAdmin]
    lookup_field = "slug"

    def update(self, request, *args, **kwargs):
        try:
            link = self.get_object()
        except InstructorLinks.DoesNotExist:
            return Response({"message": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.instructor_profile != link.instructor:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(link, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Link updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class InstructorLinksDeleteView(DestroyAPIView):
    queryset = InstructorLinks.objects.all()
    serializer_class = InstructorLinksSerializer
    permission_classes = [IsInstructorOrAdmin]
    lookup_field = "slug"

    def destroy(self, request, *args, **kwargs):
        try:
            link = self.get_object()
        except InstructorLinks.DoesNotExist:
            return Response({"message": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.instructor_profile != link.instructor:
            return Response({"message": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)
        
        link.delete()
        return Response({"message": "Link deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

