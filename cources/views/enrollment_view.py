# cources/views/enrollment_views.py
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer ,MyEnrollmentCourseSerializer,CourseEnrollmentStudentSerializer
from utils.apiResponse import success_response, error_response
from rest_framework import status
from cources.utils import calculate_course_progress, get_course_status
from rest_framework.views import APIView, Response

class EnrollCourseAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer
    
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
        

# =================== Admin View ===================
class AdminEnrollmentsAPIView(APIView):
    """
    Return all students with their enrolled courses and progress.
    Only accessible by admin users.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            enrollments = Enrollment.objects.select_related('student', 'course').all()
            students_data = {}

            for e in enrollments:
                student = e.student
                if not student:
                    continue

                student_id = student.id
                if student_id not in students_data:
                    # اسم الطالب
                    if hasattr(student, 'get_full_name'):
                        name = student.get_full_name()
                    elif hasattr(student, 'username'):
                        name = student.username
                    else:
                        name = getattr(student, 'email', 'Unknown')

                    students_data[student_id] = {
                        "student_name": name,
                        "email": getattr(student, 'email', ''),
                        "courses": []
                    }

                # progress لكل كورس
                progress = calculate_course_progress(student, e.course)

                students_data[student_id]["courses"].append({
                    "title": getattr(e.course, 'title', 'Unknown'),
                    "slug": getattr(e.course, 'slug', ''),
                    "progress": progress,
                    "status": get_course_status(progress),
                    "enrolled_at": e.enrolled_at.isoformat()
                })

            return Response(
                {"total_students": len(students_data), "students": list(students_data.values())},
                status=200
            )
        except Exception as exc:
            return error_response(
                message="Failed to retrieve enrollments",
                errors=[str(exc)],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# =================== Instructor View ===================
class InstructorEnrollmentsAPIView(APIView):
    """
    Return students enrolled in the instructor's course with progress.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug):
        try:
            instructor = getattr(request.user, 'instructor_profile', None)
            if not instructor:
                return error_response(
                    message="Instructor profile not found",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            # التأكد إن الكورس تابع للإنستراكتور
            try:
                course = Course.objects.get(slug=course_slug, instructor=instructor)
            except Course.DoesNotExist:
                return error_response(
                    message="You do not have access to this course",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            enrollments = Enrollment.objects.filter(course=course).select_related('student')

            if not enrollments.exists():
                return success_response(
                    message="No students enrolled in this course yet",
                    data=[]
                )

            students_data = []
            for e in enrollments:
                student = e.student
                if not student:
                    continue

                progress = calculate_course_progress(student, course)

                # إضافة بيانات الطالب
                if hasattr(student, 'get_full_name'):
                    name = student.get_full_name()
                elif hasattr(student, 'username'):
                    name = student.username
                else:
                    name = getattr(student, 'email', 'Unknown')

                students_data.append({
                    "student_name": name,
                    "email": getattr(student, 'email', ''),
                    "progress": progress,
                    "status": get_course_status(progress),
                    "enrolled_at": e.enrolled_at.isoformat()
                })

            return Response(
                {
                    "course": {"title": course.title, "slug": course.slug},
                    "students": students_data
                },
                status=200
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve enrollments",
                errors=[str(exc)],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )