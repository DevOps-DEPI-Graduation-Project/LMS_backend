from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from cources.models import Course, CourseRating
from cources.serializer import CourseRatingSerializer
from users.permissions import IsStudent, CanRateCourse
from utils.apiResponse import success_response, error_response

class RateCourseAPIView(CreateAPIView):
    serializer_class = CourseRatingSerializer
    permission_classes = [IsAuthenticated, IsStudent, CanRateCourse]

    def create(self, request, *args, **kwargs):
        course_slug = kwargs.get("slug")  # بدل id جبت slug

        try:
            course = Course.objects.get(slug=course_slug)  # جلب الكورس بال slug
        except Course.DoesNotExist:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # object permission (CanRateCourse)
        self.check_object_permissions(request, course)

        # prevent duplicate rating
        if CourseRating.objects.filter(course=course, student=request.user).exists():
            return error_response(
                message="You already rated this course",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Invalid rating data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(
            course=course,
            student=request.user
        )

        return success_response(
            message="Course rated successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )