from rest_framework.generics import CreateAPIView, get_object_or_404
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer 
from quizzes.models import Attempt
from users.models import Instructor
from utils.apiResponse import success_response, error_response
from rest_framework import status
from cources.utils import calculate_course_progress, calculate_student_overall_progress, get_course_status
from rest_framework.views import APIView, Response
from utils.pagination import EnrollmentPagination
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from users.permissions import IsInstructorOrAdmin
from django.db.models import Avg
from rest_framework.views import APIView
from django.db.models import Count , Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from users.models import Student
from django.db import transaction

from videos.models import VideoProgress
User = get_user_model()

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


        enrollments = (
            Enrollment.objects
            .select_related("course", "course__instructor__user")
            .filter(student=user) 
            .order_by("-enrolled_at")
        )

        if not enrollments.exists():
            return success_response(
                message="No enrollments found",
                data={"courses": []}
            )

        paginator = EnrollmentPagination()
        page = paginator.paginate_queryset(enrollments, request)

        courses_data = []
        student = Student.objects.get(user=user)

        for enrollment in page:
            course = enrollment.course

            progress = calculate_course_progress(user, course)

            instructor_name = "Unknown Instructor"

            if course.instructor is not None:
                instructor_user = course.instructor.user

                if instructor_user is not None:
                    instructor_name = (
                        f"{instructor_user.first_name} {instructor_user.last_name}".strip()
                        or instructor_user.username
                    )
            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "instructor_name": instructor_name,
                "image": request.build_absolute_uri(course.image.url) if course.image else None,
                "progress": progress,
                "status": get_course_status(progress),
                "enrolled_at": enrollment.enrolled_at.isoformat(),
            })

        return paginator.get_paginated_response(
            data=courses_data,
            total=enrollments.count(),
            message="My enrollments retrieved successfully",
            response_type="courses",
            extra_data={
                "student": {
                    "name": user.full_name if hasattr(user, 'full_name') else f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "image": request.build_absolute_uri(user.image.url) if user.image else None
                }
            }
        )

class AdminStudentsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            students = User.objects.filter(
            role="student"  
                ).annotate(
                    enrollments_count=Count("enrollments")
                ).order_by("-created_at")

            if not students.exists():
                return success_response(
                    message="No students found",
                    data={
                        "total_students": 0,
                        "students": []
                    }
                )
                
            total_students = students.count() 

            total_enrollments = Enrollment.objects.count() 

            paginator = EnrollmentPagination()
            page = paginator.paginate_queryset(students, request)

            students_data = []
            for student in page:
                first = getattr(student, "first_name", "")
                last = getattr(student, "last_name", "")

                name = (
                    f"{first} {last}".strip()
                    if first or last
                    else student.email
                )

                if getattr(student, "image", None):
                    image = request.build_absolute_uri(student.image.url) 
                else:
                    image = None

                students_data.append({
                    "student_name": name,
                    "email": student.email,
                    "is_active": student.is_active,
                    "enrollments_count": student.enrollments_count,
                    "image": image,
                    "is_verified": student.is_verified,
                    "slug": student.slug
                })

            return paginator.get_paginated_response(
                data=students_data,
                total=total_students,  
                message="Students retrieved successfully",
                response_type="students",
                extra_data={
                    "total_enrollments": total_enrollments
                }
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve students",
                errors=[str(exc)],
                status_code=500
            )
########################################
class InstructorStudentsAPIView(APIView):
    permission_classes = [IsInstructorOrAdmin]

    def get(self, request, instructor_slug):
        try:
            user = get_object_or_404(
                User,
                slug=instructor_slug,
                role="instructor"
            )

            instructor = user.instructor_profile

            students = User.objects.filter(
                enrollments__course__instructor=instructor
            ).distinct().annotate(
                enrollments_count=Count(
                    "enrollments",
                    filter=Q(enrollments__course__instructor=instructor),
                    distinct=True
                )
            ).order_by("-created_at")

            if not students.exists():
                return success_response(
                    message="No students found",
                    data={
                        "total": 0,
                        "students": []
                    }
                )

            total_enrollments = students.aggregate(
                total=Sum("enrollments_count")
            )["total"] or 0

            paginator = EnrollmentPagination()
            page = paginator.paginate_queryset(students, request)

            students_data = []
            for student in page:
                first = getattr(student, "first_name", "")
                last = getattr(student, "last_name", "")

                name = (
                    f"{first} {last}".strip()
                    if first or last
                    else student.email
                )

                image = student.image.url if getattr(student, "image", None) else None
                students_data.append({
                    "student_name": name,
                    "email": student.email,
                    "is_active": student.is_active,
                    "enrollments_count": student.enrollments_count,
                    "image": image,
                    "slug": student.slug
                })

            return paginator.get_paginated_response(
                data=students_data,
                total=students.count(),
                message="Students retrieved successfully",
                response_type="students",
                extra_data={
                    "total_enrollments": total_enrollments
                }
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve students",
                errors=[str(exc)],
                status_code=500
            )
            
# =================== Student Details (Admin) ===================
class AdminStudentDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_slug):

        # ===== Admin check =====
        if request.user.role != "admin":
            return error_response(
                "Unauthorized",
                status.HTTP_403_FORBIDDEN
            )

        # ===== Get user =====
        try:
            user = User.objects.get(
                slug=student_slug,
                role="student"
            )
        except User.DoesNotExist:
            return error_response(
                "Student not found",
                status.HTTP_404_NOT_FOUND
            )

        # ===== Check student profile =====
        student = Student.objects.filter(user=user).first()
        if student is None:
            return error_response(
                "Student profile not found",
                status.HTTP_404_NOT_FOUND
            )

        # ===== Student basic data =====
        first = getattr(user, "first_name", "")
        last = getattr(user, "last_name", "")

        name = (
            f"{first} {last}".strip()
            if first or last
            else user.email
        )

        image = (
            user.image.url
            if getattr(user, "image", None)
            else None
        )

        # ===== Student enrollments =====
        enrollments = (
            Enrollment.objects
            .select_related("course")
            .filter(student=user)
        )

        # ===== Overall progress =====
        overall_progress = calculate_student_overall_progress(
            student,
            enrollments
        )

        # ===== Courses data =====
        courses_data = []

        for enrollment in enrollments:

            course = enrollment.course

            progress = calculate_course_progress(
                user,
                course
            )

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "progress": progress,
                "status": get_course_status(progress),
                "enrolled_at": enrollment.enrolled_at,
            })

        # ===== Response =====
        return success_response(
            message="Student details retrieved successfully",
            data={
                "slug": user.slug,
                "name": name,
                "email": user.email,
                "image": image,
                "is_active": user.is_active,
                "score_avg": overall_progress,
                "total_enrollments": enrollments.count(),
                "courses": courses_data,
            }
        )
# =================== Toggle Student Status ===================
class ToggleStudentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, student_slug):
        if request.user.role != "admin":
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        try:
            student = User.objects.get(slug=student_slug, role="student")
        except User.DoesNotExist:
            return error_response("Student not found", status.HTTP_404_NOT_FOUND)

        student.is_active = not student.is_active
        student.save()

        return success_response(
            message="Student account status updated",
            data={
                "slug": student.slug,
                "is_active": student.is_active,
            }
        )
        
# =================== Delete Student ===================
class DeleteStudentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, student_slug):
        if request.user.role != "admin":
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        try:
            student = User.objects.get(slug = student_slug, role="student")
        except User.DoesNotExist:
            return error_response("Student not found", status.HTTP_404_NOT_FOUND)
      
        with transaction.atomic():
            student.delete()

        return success_response(
            message="Student deleted successfully",
            data=None
        )
        
# =================== Student Details (Instructor View) ===================
class InstructorStudentDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug, student_slug):

        # 1. Role check
        if request.user.role != "instructor":
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        # 2. Safe instructor fetch
        try:
            instructor = Instructor.objects.get(user=request.user)
        except Instructor.DoesNotExist:
            return error_response("Instructor profile not found", status.HTTP_404_NOT_FOUND)

        # 3. Course check (must belong to instructor)
        try:
            course = Course.objects.get(slug=course_slug, instructor=instructor)
        except Course.DoesNotExist:
            return error_response("Course not found", status.HTTP_404_NOT_FOUND)

        # 4. Enrollment check
        try:
            enrollment = Enrollment.objects.select_related("student").get(
                course=course,
                student__slug=student_slug
            )
        except Enrollment.DoesNotExist:
            return error_response("Student not enrolled in this course", status.HTTP_404_NOT_FOUND)

        # 5. Student data
        student = enrollment.student
        progress = calculate_course_progress(User, course)

        return success_response(
            message="Student details retrieved successfully",
            data={
                "slug": student.slug,
                "name": student.full_name,
                "email": student.email,
                "joined_at": student.created_at, 
                "course": {
                    "title": course.title,
                    "slug": course.slug,
                    "progress": progress,
                    "status": get_course_status(progress),
                    "total_videos": course.videos.count(),
                    "total_materials": course.materials.count(),
                    "total_quizzes": course.quizzes.count(),
                    "enrolled_at": enrollment.enrolled_at,
                }
            }
        )

class InstructorStudentSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_slug):

        # ===== check instructor =====
        instructor = getattr(request.user, "instructor_profile", None)
        if not instructor:
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        # ===== get student user (must be enrolled with instructor) =====
        try:
            user = User.objects.filter(
                slug=student_slug,
                enrollments__course__instructor=instructor
            ).distinct().get()
        except User.DoesNotExist:
            return error_response("Student not found", status.HTTP_404_NOT_FOUND)

        # ===== get student profile =====
        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            return error_response("Student profile not found", status.HTTP_404_NOT_FOUND)

        # ===== enrollments =====
        enrollments = Enrollment.objects.select_related("course").filter(
            student=student.user,
            course__instructor=instructor
        )

        total_enrollments = enrollments.count()

        # ===== courses data =====
        overall_progress = calculate_student_overall_progress(
            student,
            enrollments
        )
        
        courses_data = []
        for enrollment in enrollments:
            course = enrollment.course
            progress = calculate_course_progress(user, course)

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "progress": progress,
                "status": get_course_status(progress),
            })

        # ===== student name =====
        first = getattr(user, "first_name", "")
        last = getattr(user, "last_name", "")
        name = f"{first} {last}".strip() if first or last else user.email

        return success_response(
            message="Student summary retrieved successfully",
            data={
                "slug": user.slug,
                "name": name,
                "email": user.email,
                "image": user.image.url if getattr(user, "image", None) else None,
                "is_active": user.is_active,
                "total_enrollments": total_enrollments,
                "score_avg": overall_progress,
                "courses": courses_data
            }
        )