# cources/views/enrollment_views.py
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer
from utils.apiResponse import success_response, error_response
from rest_framework import status

class EnrollCourseAPIView(CreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_slug = kwargs.get("slug")
        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data={"course": course.id}, context={"request": request})
        if not serializer.is_valid():
            return error_response(
                message="Enrollment failed",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return success_response(
            message=f"You have successfully enrolled in {course.title}",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )

class MyEnrollmentsListAPIView(ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user)