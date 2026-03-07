from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course
from cources.serializer import CourseCreateSerializer, CourseSerializer
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin
from utils.apiResponse import success_response, error_response


# =================== Create Course ===================
class CourseCreateAPIView(CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsInstructorOrAdmin]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="Invalid course data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(instructor=request.user.instructor_profile)

        return success_response(
            message="Course created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )


# =================== List All Courses ===================
class CourseListAPIView(ListAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):

        courses = self.get_queryset()

        if not courses.exists():
            return success_response(
                message="No courses available",
                data=[]
            )

        serializer = self.get_serializer(courses, many=True)

        return success_response(
            message="Courses retrieved successfully",
            data=serializer.data
        )


# =================== Retrieve Course by ID ===================
class CourseRetrieveAPIView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):

        try:
            course = self.get_object()

        except Exception:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(course)

        return success_response(
            message="Course retrieved successfully",
            data=serializer.data
        )


# =================== Update Course ===================
class CourseUpdateAPIView(UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated, IsCourseOwnerOrAdmin]
    lookup_field = "id"

    def update(self, request, *args, **kwargs):

        try:
            course = self.get_object()

        except Exception:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(
            course,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return error_response(
                message="Invalid course data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return success_response(
            message="Course updated successfully",
            data=serializer.data
        )
        
# =================== Delete Course ===================
class CourseDeleteAPIView(DestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsCourseOwnerOrAdmin]
    # permission_classes = [AllowAny]
    
    lookup_field = "id"

    def destroy(self, request, *args, **kwargs):
        try:
            course = self.get_object()
        except Exception:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        course.delete()
        return success_response(
            message="Course deleted successfully",
            data=None
        )
       ##=================== List Instructor's Courses =================== 
class InstructorCoursesListAPIView(ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')
        try:
            instructor = Instructor.objects.get(slug=instructor_slug)
            return Course.objects.filter(instructor=instructor)
        except Instructor.DoesNotExist:
            return Course.objects.none()