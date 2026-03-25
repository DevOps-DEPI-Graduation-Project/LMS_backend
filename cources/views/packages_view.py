from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course, Package
from cources.serializer import CourseCreateSerializer, CourseSerializer, GetAllPackagesSerializer, PackageCreateSerializer,GetPackageDetailsSerializer
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin, IsPackageOwnerOrAdmin
from utils.apiResponse import success_response, error_response
from utils.paginationPackages import paginate_queryset
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, FloatField, Prefetch,Q
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework.filters import SearchFilter
from django.db.models.functions import Coalesce 
#===================get all packages===================

class GetAllPackagesAPIView(ListAPIView):

    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Package.objects.prefetch_related(
            Prefetch(
                'courses',
                queryset=Course.objects.prefetch_related('ratings', 'enrollments')
            ),
            "courses__instructor__user"
        ).order_by("-created_at")

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
        
class PackageRetrieveAPIView(RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = GetPackageDetailsSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        # Annotate كل كورس بالحاجات المطلوبة
        courses_qs = Course.objects.prefetch_related('ratings', 'enrollments').annotate(
            avg_rating=Coalesce(Avg('ratings__rate'), 0.0, output_field=FloatField()),
            ratings_count=Count('ratings'),
            students_count=Count('enrollments', distinct=True)
        )

        # Prefetch الكورسات مع annotations
        return Package.objects.prefetch_related(
            Prefetch('courses', queryset=courses_qs)
        ).select_related('instructor', 'instructor__user').annotate(
            avg_rating=Coalesce(Avg('courses__ratings__rate'), 0.0, output_field=FloatField()),
            ratings_count=Count('courses__ratings'),
            students_count=Count('courses__enrollments', distinct=True)
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            package = self.get_queryset().get(slug=self.kwargs.get('slug'))
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(package)
        return success_response(
            message="Package retrieved successfully",
            data=serializer.data
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
    