from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from cources.models import Enrollment, Course
from cources.serializer import EnrollmentSerializer ,MyEnrollmentCourseSerializer,CourseEnrollmentStudentSerializer
from utils.apiResponse import success_response, error_response
from rest_framework import status
from cources.utils import calculate_course_progress, get_course_status
from rest_framework.views import APIView, Response
from utils.pagination import EnrollmentPagination
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated     
from django.db.models import Avg
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count , Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser


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
            .select_related("course")
            .filter(student=user)
            .order_by("-enrolled_at")
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
            total=enrollments.count(),
            message="My enrollments retrieved successfully",
            response_type="courses",
            extra_data={
                "student": {
                    "name": user.full_name,
                    "email": user.email,
                    "image": user.image.url if user.image else None
                }
            }
        )
# # =================== Admin View ===================
# class AdminEnrollmentsAPIView(APIView):
#     permission_classes = [IsAdminUser]

#     def get(self, request):
#         try:
#             enrollments = Enrollment.objects.select_related("student", "course").all().order_by("-enrolled_at")
#             if not enrollments.exists():
#                 return success_response(
#                     message="No enrollments found",
#                     data={
#                         "total_students": 0,
#                         "total_pages": 0,
#                         "current_page": 1,
#                         "students": []
#                     }
#                 )

#             paginator = EnrollmentPagination()
#             page = paginator.paginate_queryset(enrollments, request)

#             students_dict = {}
#             for e in page:
#                 student = e.student
#                 if not student:
#                     continue
#                 student_id = student.id
#             if student_id not in students_dict:
#                 first = getattr(student, 'first_name', '')
#                 last = getattr(student, 'last_name', '')

#                 if first or last:
#                     name = f"{first} {last}".strip()
#                 else:
#                     name = getattr(student, 'email', 'Unknown Student') 
                
#                 students_dict[student_id] = {
#                     "student_name": name,
#                     "email": getattr(student, "email", ""),
#                     "courses": []
#                 }
#                 progress = calculate_course_progress(student, e.course)
#                 students_dict[student_id]["courses"].append({
#                     "title": e.course.title,
#                     "slug": e.course.slug,
#                     "progress": progress,
#                     "status": get_course_status(progress),
#                     "enrolled_at": e.enrolled_at.isoformat()
#                 })

#             return paginator.get_paginated_response(
#                 data=list(students_dict.values()),
#                 total=len(students_dict),
#                 message="Admin enrollments retrieved successfully",
#                 response_type="students"
#             )

#         except Exception as exc:
#             return error_response(
#                 message="Failed to retrieve enrollments",
#                 errors=[str(exc)],
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

# # =================== Instructor View ===================
# class InstructorEnrollmentsAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, course_slug):
#         try:
#             instructor = getattr(request.user, "instructor_profile", None)
#             if not instructor:
#                 return error_response(
#                     message="Instructor profile not found",
#                     status_code=status.HTTP_403_FORBIDDEN
#                 )

#             try:
#                 course = Course.objects.get(slug=course_slug, instructor=instructor)
#             except Course.DoesNotExist:
#                 return error_response(
#                     message="You do not have access to this course",
#                     status_code=status.HTTP_404_NOT_FOUND
#                 )

#             enrollments = Enrollment.objects.filter(course=course).select_related("student").order_by("-enrolled_at")
#             if not enrollments.exists():
#                 return success_response(
#                     message="No students enrolled in this course yet",
#                     data={
#                         "total_students": 0,
#                         "total_pages": 0,
#                         "current_page": 1,
#                         "students": []
#                     }
#                 )

#             paginator = EnrollmentPagination()
#             page = paginator.paginate_queryset(enrollments, request)

#             students_data = []
#             for e in page:
#                 student = e.student
#                 if not student:
#                     continue
#                 progress = calculate_course_progress(student, course)
#                 name = None
#                 first = getattr(student, 'first_name', '')
#                 last = getattr(student, 'last_name', '')

#                 if first or last:
#                     name = f"{first} {last}".strip()
#                 else:
#                     name = getattr(student, 'email', 'Unknown Student') 
                         
#                 students_data.append({
#                     "student_name": name,
#                     "email": getattr(student, "email", ""),
#                     "progress": progress,
#                     "status": get_course_status(progress),
#                     "enrolled_at": e.enrolled_at.isoformat()
#                 })

#             return paginator.get_paginated_response(
#             data=students_data,
#             total=len(students_data),
#             message="Instructor enrollments retrieved successfully",
#             response_type="students"
#             )

#         except Exception as exc:
#             return error_response(
#                 message="Failed to retrieve enrollments",
#                 errors=[str(exc)],
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )

class AdminStudentsAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            students = User.objects.filter(
                enrollments__isnull=False
            ).distinct().annotate(
                enrollments_count=Count("enrollments", distinct=True)
            ).order_by("-created_at")
            
            if not students.exists():
                return success_response(
                    message="No students found",
                    data={
                        "total": 0,
                        "students": []
                    }
                )
                
            totalEnrollments = students.aggregate(
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
                image = student.image.url if getattr(student,"image",None) else None
                students_data.append({
                    "student_name": name,
                    "email": student.email,
                    "is_active": student.is_active,
                    "enrollments_count": student.enrollments_count,
                    "image": image,
                })

            return paginator.get_paginated_response(
                data=students_data,
                total=students.count(),
                message="Students retrieved successfully",
                response_type="students",
                extra_data={
                    "total_enrollments":totalEnrollments
                }
            )

        except Exception as exc:
            return error_response(
                message="Failed to retrieve students",
                errors=[str(exc)],
                status_code=500
            )
                 


class InstructorStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            instructor = getattr(request.user, "instructor_profile", None)
            if not instructor:
                return error_response(
                    message="Instructor profile not found",
                    status_code=403
                )

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
            
            totalEnrollments = students.aggregate(
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
                
                image = student.image.url if getattr(student,"image",None) else None

                students_data.append({
                    "student_name": name,
                    "email": student.email,
                    "is_active": student.is_active,
                    "enrollments_count": student.enrollments_count,
                    "image": image
                })

                
            return paginator.get_paginated_response(
                data=students_data,
                total=students.count(),
                message="Students retrieved successfully",
                response_type="students",
                extra_data={
                    "total_enrollments":totalEnrollments
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
        if request.user.role != "admin":
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        try:
            student = User.objects.get(slug=student_slug, role="student")
        except User.DoesNotExist:
            return error_response("Student not found", status.HTTP_404_NOT_FOUND)

        
        first = getattr(student, "first_name", "")
        last = getattr(student, "last_name", "")
        name = f"{first} {last}".strip() if first or last else student.email
        
        image = student.image.url if getattr(student,"image",None) else None
        
        enrollments = Enrollment.objects.select_related("course").filter(student=student)

        courses_data = []
        total_progress = 0

        for enrollment in enrollments:
            progress = calculate_course_progress(student, enrollment.course)
            total_progress += progress

            courses_data.append({
                "title": enrollment.course.title,
                "slug": enrollment.course.slug,
                "progress": progress,
                "status": get_course_status(progress),
                "last_activity": enrollment.updated_at,
            })

        avg_score = round(total_progress / enrollments.count(), 2) if enrollments.exists() else 0

        return success_response(
            message="Student details retrieved successfully",
            data={
                "slug": student.slug,
                "name": name,
                "email": student.email,
                "image":image,
                "is_active": student.is_active,
                # "joined_at": student.date_joined,
                "avg_score": avg_score,
                "total_enrollments": enrollments.count(),
                "courses": courses_data
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
                "is_active": student.is_active
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

        student.delete()

        return success_response(
            message="Student deleted successfully",
            data=None
        )
        
# =================== Student Details (Instructor View) ===================
class InstructorStudentDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug, student_slug):

        if request.user.role != "instructor":
            return error_response("Unauthorized", status.HTTP_403_FORBIDDEN)

        try:
            course = Course.objects.get(slug=course_slug, instructor=request.user)
        except Course.DoesNotExist:
            return error_response("Course not found", status.HTTP_404_NOT_FOUND)

        try:
            enrollment = Enrollment.objects.select_related("student").get(
                course=course,
                student__slug=student_slug
            )
        except Enrollment.DoesNotExist:
            return error_response("Student not enrolled in this course", status.HTTP_404_NOT_FOUND)

        student = enrollment.student
        progress = calculate_course_progress(student, course)

        return success_response(
            message="Student details retrieved successfully",
            data={
                "slug": student.slug,
                "name": student.full_name,
                "email": student.email,
                "joined_at": student.date_joined,
                "course": {
                    "title": course.title,
                    "slug": course.slug,
                    "progress": progress,
                    "status": get_course_status(progress),
                    "total_lessons": course.lectures.count(),
                    "completed_lessons": enrollment.completed_lessons.count(),
                    "last_activity": enrollment.updated_at
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

        # ===== get student (must be enrolled with instructor) =====
        try:
            student = User.objects.filter(
                slug=student_slug,
                enrollments__course__instructor=instructor
            ).distinct().get()
        except User.DoesNotExist:
            return error_response("Student not found", status.HTTP_404_NOT_FOUND)

        # ===== enrollments =====
        enrollments = Enrollment.objects.select_related("course").filter(
            student=student,
            course__instructor=instructor
        )

        total_enrollments = enrollments.count()

        # ===== average score (ratings) =====
        avg_score = (
            enrollments.aggregate(
                avg=Avg("course__ratings__rate")
            )["avg"] or 0
        )

        # ===== courses data =====
        courses_data = []
        for enrollment in enrollments:
            course = enrollment.course
            progress = calculate_course_progress(student, course)

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "progress": progress,
                "status": get_course_status(progress),
            })

        # ===== student name =====
        first = getattr(student, "first_name", "")
        last = getattr(student, "last_name", "")
        name = f"{first} {last}".strip() if first or last else student.email

        return success_response(
            message="Student summary retrieved successfully",
            data={
                "slug": student.slug,
                "name": name,
                "email": student.email,
                "image": student.image.url if student.image else None,
                "is_active": student.is_active,
                "total_enrollments": total_enrollments,
                "average_score": round(avg_score, 2),
                "courses": courses_data
            }
        )
        