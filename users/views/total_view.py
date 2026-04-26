from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from users.models import Student,Instructor
from cources.models import Course,Enrollment

from users.permissions import IsAdmin, IsInstructorOrAdmin
from utils.apiResponse import success_response,error_response

class TotalAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            total_students = Student.objects.count()
            total_instructors = Instructor.objects.count()
            total_active_courses = Course.objects.filter(is_active=True).count()
            total_enrollments = Enrollment.objects.count()
            total_courses = Course.objects.count()

            data = {
                "total_students": total_students,
                "total_instructors": total_instructors,
                "total_enrollments": total_enrollments,
                "total_courses": total_courses,
                "total_active_courses": total_active_courses
            }

            return success_response("Totals fetched successfully", data)

        except Exception as e:
            return error_response(
                "Failed to fetch totals",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
###=======================the total for specific instructor=================================

class InstructorTotalsBySlugAPIView(APIView):
    permission_classes = [IsInstructorOrAdmin]

    def get(self, request, slug):
        try:
            instructor = Instructor.objects.get(user__slug=slug)

            total_courses = instructor.courses.count()
            total_active_courses = instructor.courses.filter(is_active=True).count()
            total_enrolled_students = Enrollment.objects.filter(
                course__instructor=instructor
            ).values('student').distinct().count()
            total_packages = instructor.packages.count(),

            data = {
                "instructor_slug": instructor.user.slug,
                # "instructor_first_name": instructor.user.first_name,
                # "instructor_last_name": instructor.user.last_name,
                "total_courses": total_courses,
                "total_active_courses": total_active_courses,
                "total_enrolled_students": total_enrolled_students,
                "total_packages": total_packages,
            }

            return success_response("Instructor totals fetched successfully", data)

        except Instructor.DoesNotExist:
            return error_response(
                "Instructor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                "Failed to fetch instructor totals",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        #=================================
        
class TotalCourseDetailsAPIView(APIView):
    permission_classes=[IsInstructorOrAdmin]
    
    def get(self,request,slug):
        try:
            course=Course.objects.get(slug=slug)
            total_Materials=course.materials.count()
            total_Videos=course.videos.count()
            total_Quizzes=course.quizzes.count()
            data={
                "course_slug":course.slug,
                "course_title":course.title,
                "total_Materials":total_Materials,
                "total_Videos":total_Videos,
                "total_Quizzes":total_Quizzes,
                "total_Students":course.enrollments.count()
            }
            return success_response("Course details fetched successfully",data)
        except Course.DoesNotExist:
            return error_response(
                "Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
