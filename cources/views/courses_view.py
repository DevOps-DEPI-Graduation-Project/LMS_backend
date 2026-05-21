from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course, CourseRating, Enrollment
from cources.serializer import CourseCreateSerializer, CourseSerializer,InstructorCourseSerializer, InstructorsProfileSerializer ,CourseRatingSerializer, CourseDetailSerializer, CourseStudentSerializer
from users.models import Instructor
from users.permissions import IsAdmin, IsInstructorOrAdmin, IsCourseOwnerOrAdmin
from utils.apiResponse import success_response, error_response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count , Exists , OuterRef , Value , BooleanField
from django.db.models.functions import Coalesce, Concat
from utils.pagination import EnrollmentPagination  
from django.db.models import F
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

# =================== Create Course ===================
class CourseCreateAPIView(CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsInstructorOrAdmin]
    # permission_classes = [AllowAny]

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


# ---------------- Pagination Class ----------------
class CoursePagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size' 
    max_page_size = 50

# ---------------- List All Courses API ----------------
class CourseListAPIView(ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    pagination_class = CoursePagination

    def get_queryset(self):
        user = self.request.user

        queryset = Course.objects.select_related("instructor__user").annotate(
            avg_rating=Avg("ratings__rate"),
            ratings_count=Count("ratings"),
            students_count=Count("enrollments", distinct=True)
    ).order_by('-created_at')
        
    # ===== Student with token =====
        if user.is_authenticated and getattr(user,"role",None)=="student":
            queryset = queryset.annotate(
                is_enrolled=Exists(
                    Enrollment.objects.filter(
                        student=user,
                        course=OuterRef("pk")
                    )
                )
            )
        # ===== Guest or non-student =====
        else:
            queryset = queryset.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return success_response(
                message="No courses available",
                data={
                    "total_courses": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "courses": []
                }
            )

        # paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # fallback (rarely used)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Courses retrieved successfully",
            data={
                "total_courses": len(serializer.data),
                "total_pages": 1,
                "current_page": 1,
                "courses": serializer.data
            }
        )

    def get_paginated_response(self, data):
        return success_response(
            message="Courses retrieved successfully",
            data={
                "total_courses": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "courses": data
            }
        )
        
# ============= course retrieve =============
class CourseRetrieveAPIView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Course.objects.select_related("instructor__user").annotate(
            avg_rating=Avg("ratings__rate"),
            ratings_count=Count("ratings")
        )
        user = self.request.user
        
        if user.is_authenticated and getattr(user, "role", None) == "student":
            queryset = queryset.annotate(
                is_enrolled=Exists(
                    Enrollment.objects.filter(
                        student=user,
                        course=OuterRef("pk")
                    )
                )
            )
        else:
            queryset = queryset.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )
        return queryset

    def retrieve(self, _request, *_args, **_kwargs):
        try:
            course = self.get_object()
        except Course.DoesNotExist:
            return error_response(
                message="Course not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(course)

        return success_response(
            message="Course retrieved successfully",
            data={
                **serializer.data,
                "is_active": course.is_active  
            }
        )
        
# ============== course students ==============

class CourseStudentsAPIView(ListAPIView):
    serializer_class = CourseStudentSerializer
    pagination_class = EnrollmentPagination
    permission_classes = [IsAuthenticated,IsCourseOwnerOrAdmin]

    def get_course(self):
        course_slug = self.kwargs.get("course_slug")
        return get_object_or_404(Course, slug=course_slug)

    def get_queryset(self):
        course = self.get_course()

        return (
            Enrollment.objects
            .filter(course=course)
            .select_related("student")
            .order_by("-enrolled_at")
        )

    def list(self, request, *args, **kwargs):
        course = self.get_course()

        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        
        total_students = queryset.count()

        total_videos = course.videos.count() if hasattr(course, "videos") else 0
        total_materials = course.materials.count() if hasattr(course, "materials") else 0

        return self.paginator.get_paginated_response(
            data=serializer.data,
            message="Course students retrieved successfully",
            response_type="students",
            extra_data={
                "total_students": total_students,
                "total_videos": total_videos,
                "total_materials": total_materials,
                "course_slug": course.slug,
                "course_title": course.title,
            }
        )
        
# =================== Update Course ===================
class CourseUpdateAPIView(UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated, IsCourseOwnerOrAdmin]
    lookup_field = "slug"

    def update(self, request, *args, **kwargs):

        try:
            course = self.get_object()

        except Course.DoesNotExist:
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
    lookup_field = "slug"

    def destroy(self, request, *args, **kwargs):
        try:
            course = self.get_object()
            
            with transaction.atomic():
                if hasattr(course, 'hard_delete'):
                    course.hard_delete()
                else:
                    course.delete()

            return success_response(
                message="Course deleted successfully",
                data=None,
                status_code=status.HTTP_200_OK 
            )
            
        except Exception as e:
            return error_response(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )

class InstructorCoursesListAPIView(ListAPIView):
    serializer_class = InstructorCourseSerializer
    permission_classes = [IsInstructorOrAdmin]
    pagination_class = CoursePagination

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')

        instructor = get_object_or_404(
            Instructor,
            user__slug=instructor_slug
        )

        return Course.objects.filter(instructor=instructor).annotate(
            students_count=Count('enrollments', distinct=True),
            ratings_count=Count('ratings', distinct=True)
        ).order_by('-created_at')
        
    def get_paginated_response(self, data):
        return success_response(
            message="Instructor's courses retrieved successfully",
            data={
                "total_courses": self.paginator.page.paginator.count,
                "total_pages": self.paginator.page.paginator.num_pages,
                "current_page": self.paginator.page.number,
                "courses": data
            }
        )


    
        
#====================all instructors profile==================

class AllInstructorsProfileAPIView(ListAPIView):
    queryset = Instructor.objects.select_related("user").all()
    serializer_class = InstructorsProfileSerializer
    permission_classes = [IsAdmin]
    
    def list(self, request, *args, **kwargs):

        instructors = self.get_queryset()

        if not instructors.exists():
            return success_response(
                message="No instructors available",
                data=[]
            )

        serializer = self.get_serializer(instructors, many=True)

        return success_response(
            message="Instructors retrieved successfully",
            data=serializer.data
        )
        


##========================get instructor profile========================
class InstructorProfileAPIView(RetrieveAPIView):
    queryset=Instructor.objects.select_related("user").all()
    serializer_class=InstructorsProfileSerializer
    permission_classes=[AllowAny]
    lookup_field="user__slug"
    lookup_url_kwarg = "instructor_slug"  
    def retrieve(self, request, *args, **kwargs):

        try:
            instructor = self.get_object()

        except Instructor.DoesNotExist:
            return error_response(
                message="Instructor not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instructor)

        return success_response(
            message="Instructor profile retrieved successfully",
            data=serializer.data
        )

########## Top rated ###########
class TopRatedCoursesAPIView(ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = (
            Course.objects.select_related("instructor__user")
            .filter(is_active=True)
            .annotate(
                avg_rating=Avg("ratings__rate"),
                ratings_count=Count("ratings"),
                students_count=Count("enrollments", distinct=True)
            )
            .order_by("-avg_rating", "-created_at")
        )

        limit = self.request.query_params.get("limit")
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            serializer = self.get_serializer(queryset, many=True)

            return success_response(
                message="Top rated courses retrieved successfully",
                data=serializer.data
            )

        except Exception as e:
            return error_response(
                message="Failed to retrieve top rated courses",
                errors=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
            
            