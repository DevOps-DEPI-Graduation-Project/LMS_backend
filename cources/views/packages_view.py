from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course, Enrollment, Package
from cources.serializer import CourseCreateSerializer, CourseSerializer, GetAllPackagesSerializer, PackageCreateSerializer,GetPackageDetailsSerializer
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin, IsPackageOwnerOrAdmin
from utils.apiResponse import success_response, error_response
from utils.paginationPackages import paginate_queryset
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, FloatField, Prefetch, Q, Exists, OuterRef, Value, BooleanField, Case, When, F
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import SearchFilter
from django.db.models.functions import Coalesce 
#===================get all packages===================

class GetAllPackagesAPIView(ListAPIView):

    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user

        queryset = Package.objects.prefetch_related(
            Prefetch(
                'courses',
                queryset=Course.objects.prefetch_related('ratings', 'enrollments')
            ),
            "courses__instructor__user"
        ).order_by("-created_at")

        if user.is_authenticated and getattr(user, "role", None) == "student":
            queryset = queryset.annotate(
                total_courses=Count('courses', distinct=True),
                enrolled_courses_count=Count(
                    'courses__enrollments',
                    filter=Q(courses__enrollments__student=user),
                    distinct=True
                ),
                is_enrolled=Case(
                    When(
                        total_courses=F('enrolled_courses_count'),
                        total_courses__gt=0,
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        else:
            queryset = queryset.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )

        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category:
            queryset = queryset.filter(
                courses__category__iexact=category
            )

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)|
                Q(instructor__user__first_name__icontains=search)
            )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        return paginate_queryset(
            queryset=queryset,
            request=request,
            serializer_class=self.get_serializer_class(),
            data_key="packages",
            total_key="total_packages",
            message="Packages retrieved successfully"
        )
#=================== Create Package ===================
class PackageCreateAPIView(CreateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsInstructorOrAdmin]
    # permission_classes=[AllowAny]
    
    def create(self,request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid package data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(instructor=request.user.instructor_profile)
        return success_response(
            message="Package created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
from django.db.models import Avg, Count, Exists, OuterRef, Value, BooleanField, FloatField
from django.db.models.functions import Coalesce
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
# from .models import Package, Course, Enrollment
# from .serializers import GetPackageDetailsSerializer
# from .responses import success_response, error_response
from django.db.models import Prefetch

class PackageRetrieveAPIView(RetrieveAPIView):
    serializer_class = GetPackageDetailsSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):

        user = self.request.user
        student_obj = getattr(user, "student", None) if user.is_authenticated and getattr(user, "role", None) == "student" else None

        # ===== Annotate Courses =====
        courses_qs = (
            Course.objects.select_related('instructor__user')
            .annotate(
                avg_rating=Coalesce(Avg('ratings__rate'), 0.0, output_field=FloatField()),
                ratings_count=Count('ratings'),
                students_count=Count('enrollments', distinct=True)
            )
            .prefetch_related('ratings', 'enrollments')
        )

        # Annotate is_enrolled only if student exists
        if student_obj:
            courses_qs = courses_qs.annotate(
                is_enrolled=Exists(
                    Enrollment.objects.filter(
                        student=student_obj,
                        course=OuterRef('pk')
                    )
                )
            )
        else:
            courses_qs = courses_qs.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )

        # ===== Prefetch Courses + Annotate Package =====
        return (
            Package.objects
            .prefetch_related(
                Prefetch('courses', queryset=courses_qs)
            )
            .select_related('instructor', 'instructor__user')
            .annotate(
                avg_rating=Coalesce(
                    Avg('courses__ratings__rate'),
                    0.0,
                    output_field=FloatField()
                ),
                ratings_count=Count('courses__ratings'),
                students_count=Count(
                    'courses__enrollments__student',
                    distinct=True
                )
            )
        )

    def retrieve(self, request, *args, **kwargs):
        print("USER:", request.user)
        print("AUTH:", request.auth)
        try:
            package = self.get_queryset().get(slug=self.kwargs["slug"])
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=404
            )

        user = request.user
        student_obj = getattr(user, "student", None) if user.is_authenticated and getattr(user, "role", None) == "student" else None

        # ===== Prepare Courses Data =====
        courses_data = []
        enrolled_courses_count = 0
        for course in package.courses.all():
            is_enrolled = getattr(course, 'is_enrolled', None)
            if is_enrolled:
                enrolled_courses_count += 1

            instructor_name = None
            if getattr(course, 'instructor', None) and getattr(course.instructor, 'user', None):
                instructor_name = ' '.join(filter(None, [course.instructor.user.first_name, course.instructor.user.last_name])).strip() or getattr(course.instructor.user, 'email', None)

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "image": course.image.url if course.image else None,
                "avg_rating": getattr(course, 'avg_rating', 0.0),
                "ratings_count": getattr(course, 'ratings_count', 0),
                "students_count": getattr(course, 'students_count', 0),
                "is_enrolled": is_enrolled,
                "instructor_name": instructor_name,
            })

        # ===== Package is_enrolled =====
        package_is_enrolled = None
        total_courses = package.courses.count()
        if student_obj and total_courses > 0:
            package_is_enrolled = enrolled_courses_count == total_courses

        return success_response(
            message="Package retrieved successfully",
            data={
                "title": package.title,
                "slug": package.slug,
                "description": package.description,
                "price": package.price,
                "avg_rating": package.avg_rating,
                "ratings_count": package.ratings_count,
                "students_count": package.students_count,
                "courses_count": total_courses,
                "is_enrolled": package_is_enrolled,
                "courses": courses_data,
            }
        )
##=================== Update Package ===================

class PackageUpdateAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):
        try:
            package=self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer=self.get_serializer(
            package, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Invalid package data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return success_response(
            message="Package updated successfully",
            data=serializer.data
        )
        
        
#=================== Delete Package ===================
class PackageDeleteAPIView(DestroyAPIView):
    queryset=Package.objects.all()
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def destroy(self, request, *args, **kwargs):
      try:
          package=self.get_object()
      except Package.DoesNotExist:
          return error_response(
              message="Package not found",
              status_code=status.HTTP_404_NOT_FOUND
             )  
      package.delete()
      return success_response(
            message="Package deleted successfully",
            data=None
        )
      
    #   instructor list of packages
    
class InstructorPackagesListAPIView(ListAPIView):
    
    Package.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.prefetch_related('ratings', 'enrollments'))
    )
    
    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')
        try:
            instructor = Instructor.objects.get(user__slug=instructor_slug)
            return Package.objects.filter(instructor=instructor).prefetch_related(
                "courses", "courses__instructor__user"
            ).order_by("-created_at")
        except Instructor.DoesNotExist:
            return Package.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        return paginate_queryset(
            queryset=queryset,
            request=request,
            serializer_class=self.get_serializer_class(),
            data_key="packages",
            total_key="total_packages",
            message="Instructor packages retrieved successfully"
        )
    
#====================add course to package===================
class AddCourseToPackageAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    # permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):

        try:
            package = self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        course_slugs = request.data.get('course_slugs', [])
        

        courses = Course.objects.filter(slug__in=course_slugs, instructor=package.instructor)

        if not courses.exists():
            return error_response(
                message="No valid courses found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        package.courses.add(*courses)

        return success_response(
            message="Courses added to package successfully"
        )
        
        
# =================== Enroll Package ===================
class EnrollPackageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, package_slug):
        user = request.user

        if user.role != "student":
            return error_response(
                message="Only students can enroll in packages",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            package = Package.objects.prefetch_related("courses").get(
                slug=package_slug,
            )
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        enrolled_courses = []
        for course in package.courses.all():
            enrollment, created = Enrollment.objects.get_or_create(
                student=user,
                course=course
            )
            enrolled_courses.append(course)

        return success_response(
            message="Package enrolled successfully",
            data={
                "package": {
                    "title": package.title,
                    "slug": package.slug,
                    "is_enrolled": True,
                    "courses": [
                        {
                            "title": course.title,
                            "slug": course.slug,
                            "image": course.image.url if course.image else None,
                            "is_enrolled": True
                        }
                        for course in enrolled_courses
                    ]
                }
            }
        ) 
        
        
##===================get courses in package===================
class PackageCoursesListAPIView(ListAPIView):
    
    Package.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.prefetch_related('ratings', 'enrollments'))
    )
    
    queryset=Package.objects.all()
    serializer_class=CourseSerializer
    permission_classes=[AllowAny]
    def get_queryset(self):
        package_slug=self.kwargs.get('slug')
        try:
            package=self.queryset.get(slug=package_slug)
            return package.courses.annotate(
                avg_rating=Avg('ratings__rate'),
                ratings_count=Count('ratings'),
                students_count=Count('enrollments')
            )
        except Package.DoesNotExist:
            return Course.objects.none()
        
        
#=================== Remove Course from Package ===================
class RemoveCourseFromPackageAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):

        try:
            package = self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        course_slugs = request.data.get('course_slugs', [])

        courses = Course.objects.filter(slug__in=course_slugs, instructor=package.instructor)

        if not courses.exists():
            return error_response(
                message="No valid courses found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        package.courses.remove(*courses)

        return success_response(
            message="Courses removed from package successfully",
        )
    