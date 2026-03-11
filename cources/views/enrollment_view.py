# cources/views/enrollment_views.py
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer ,MyEnrollmentCourseSerializer
from utils.apiResponse import success_response, error_response
from rest_framework import status
from cources.utils import calculate_course_progress, get_course_status
from rest_framework.views import APIView


class EnrollCourseAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_slug = kwargs.get("slug")
        
        if user.role != "student":
            return error_response(
                message="Enrollment failed",
                errors=["Only students can enroll in courses"],
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            course = Course.objects.get(slug=course_slug)
        except Course.DoesNotExist:
            return error_response(
                message="Enrollment failed",
                errors=["Course not found"],
                status_code=status.HTTP_404_NOT_FOUND
            )

        if not course.is_active:
            return error_response(
                message="Enrollment failed",
                errors=["Course is not available for enrollment"],
                status_code=status.HTTP_400_BAD_REQUEST
            )

        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course
        )

        if not created:
            return error_response(
                message="Enrollment failed",
                errors=["You are already enrolled in this course"],
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return success_response(
            message=f"You have successfully enrolled in {course.title}",
            data={
                "course": {
                    "title": course.title,
                    "slug": course.slug
                }
            },
            status_code=status.HTTP_201_CREATED
        )

class MyEnrollmentsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "student":
            return error_response(
                message="Only students can view enrollments",
                status_code=status.HTTP_403_FORBIDDEN
            )

        enrollments = Enrollment.objects.select_related("course").filter(student=user)

        if not enrollments.exists():
            return success_response(
                message="You have no enrollments yet",
                data={
                    "total_courses": 0,
                    "courses": []
                }
            )

        courses_data = []

        for enrollment in enrollments:
            course = enrollment.course
            progress = calculate_course_progress(user, course)

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "image": course.image.url if course.image else None,
                "progress": progress,
                "status": get_course_status(progress),
                "enrolled_at": enrollment.enrolled_at.isoformat(),
            })

        return success_response(
            message="My enrollments retrieved successfully",
            data={
                "total_courses": len(courses_data),
                "courses": courses_data
            }
        )