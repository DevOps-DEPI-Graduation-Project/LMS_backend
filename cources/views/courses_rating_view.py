from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from cources.models import Course, CourseRating, Enrollment
from cources.serializer import CourseRatingSerializer
from users.permissions import IsStudent
from utils.apiResponse import success_response, error_response

class RateCourseAPIView(CreateAPIView):
    serializer_class = CourseRatingSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def create(self, request, **kwargs):
        course_slug = kwargs.get("slug")

        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        is_enrolled = Enrollment.objects.filter(
            course=course,
            student=request.user
        ).exists()

        if not is_enrolled:
            return error_response(
                message="You must be enrolled in this course to rate it",
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Invalid rating data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        rating_value = serializer.validated_data.get("rate")

        rating_obj, created = CourseRating.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={
                "rate": rating_value
            }
        )

        return success_response(
            message="Rating added successfully" if created else "Rating updated successfully",
            data={
                "rate": rating_obj.rate,
            },
            status_code=status.HTTP_200_OK
        )