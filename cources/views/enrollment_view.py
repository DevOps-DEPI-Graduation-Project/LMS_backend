# cources/views/enrollment_views.py
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer ,MyEnrollmentCourseSerializer,CourseEnrollmentStudentSerializer
from utils.apiResponse import success_response, error_response
from rest_framework import status
from cources.utils import calculate_course_progress, get_course_status
from rest_framework.views import APIView, Response
from utils.pagination import EnrollmentPagination

class EnrollCourseAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class=EnrollmentSerializer
    
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

# =================== My Enrollments (Student View) ===================
class MyEnrollmentsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "student":
            return error_response(
                message="Only students can view enrollments",
                status_code=status.HTTP_403_FORBIDDEN
            )

        enrollments = Enrollment.objects.select_related("course").filter(student=user).order_by("-enrolled_at")
        if not enrollments.exists():
            return success_response(
                message="You have no enrollments yet",
                data={
                    "total_courses": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "courses": []
                }
            )

        paginator = EnrollmentPagination()
        page = paginator.paginate_queryset(enrollments, request)

        courses_data = []
        for enrollment in page:
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
            
        return paginator.get_paginated_response(
            data=courses_data,
            total=len(enrollments),
            message="My enrollments retrieved successfully",
            response_type="courses"
        )

# =================== Admin View ===================
class AdminEnrollmentsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            enrollments = Enrollment.objects.select_related("student", "course").all().order_by("-enrolled_at")
            if not enrollments.exists():
                return success_response(
                    message="No enrollments found",
                    data={
                        "total_students": 0,
                        "total_pages": 0,
                        "current_page": 1,
                        "students": []
                    }
                )

            paginator = EnrollmentPagination()
            page = paginator.paginate_queryset(enrollments, request)

            students_dict = {}
            for e in page:
                student = e.student
                if not student:
                    continue
                student_id = student.id
            if student_id not in students_dict:
                first = getattr(student, 'first_name', '')
                last = getattr(student, 'last_name', '')

                if first or last:
                    name = f"{first} {last}".strip()
                else:
                    name = getattr(student, 'email', 'Unknown Student') 
                
                students_dict[student_id] = {
                    "student_name": name,
                    "email": getattr(student, "email", ""),
                    "courses": []
                }
                progress = calculate_course_progress(student, e.course)
                students_dict[student_id]["courses"].append({
                    "title": e.course.title,
                    "slug": e.course.slug,
                    "progress": progress,
                    "status": get_course_status(progress),
                    "enrolled_at": e.enrolled_at.isoformat()
                })

            return paginator.get_paginated_response(
                data=list(students_dict.values()),
                total=len(students_dict),
                message="Admin enrollments retrieved successfully",
                response_type="students"
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve enrollments",
                errors=[str(exc)],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =================== Instructor View ===================
class InstructorEnrollmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug):
        try:
            instructor = getattr(request.user, "instructor_profile", None)
            if not instructor:
                return error_response(
                    message="Instructor profile not found",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            try:
                course = Course.objects.get(slug=course_slug, instructor=instructor)
            except Course.DoesNotExist:
                return error_response(
                    message="You do not have access to this course",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            enrollments = Enrollment.objects.filter(course=course).select_related("student").order_by("-enrolled_at")
            if not enrollments.exists():
                return success_response(
                    message="No students enrolled in this course yet",
                    data={
                        "total_students": 0,
                        "total_pages": 0,
                        "current_page": 1,
                        "students": []
                    }
                )

            paginator = EnrollmentPagination()
            page = paginator.paginate_queryset(enrollments, request)

            students_data = []
            for e in page:
                student = e.student
                if not student:
                    continue
                progress = calculate_course_progress(student, course)
                name = None
                first = getattr(student, 'first_name', '')
                last = getattr(student, 'last_name', '')

                if first or last:
                    name = f"{first} {last}".strip()
                else:
                    name = getattr(student, 'email', 'Unknown Student') 
                         
                students_data.append({
                    "student_name": name,
                    "email": getattr(student, "email", ""),
                    "progress": progress,
                    "status": get_course_status(progress),
                    "enrolled_at": e.enrolled_at.isoformat()
                })

            return paginator.get_paginated_response(
            data=students_data,
            total=len(students_data),
            message="Instructor enrollments retrieved successfully",
            response_type="students"
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve enrollments",
                errors=[str(exc)],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )