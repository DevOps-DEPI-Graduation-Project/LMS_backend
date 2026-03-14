from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course, Package
from cources.serializer import CourseCreateSerializer, CourseSerializer, GetAllPackagesSerializer, PackageCreateSerializer,GetPackageDetailsSerializer
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin, IsPackageOwnerOrAdmin
from utils.apiResponse import success_response, error_response


#===================get all packages===================

class GetAllPackagesAPIView(ListAPIView):
    queryset = Package.objects.all()
    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]
    
    def list(self, request, *args, **kwargs):

        packages = self.get_queryset()

        if not packages.exists():
            return success_response(
                message="No packages available",
                data=[]
            )

        serializer = self.get_serializer(packages, many=True)

        return success_response(
            message="Packages retrieved successfully",
            data=serializer.data
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
        
#===================get package by id===================
class PackageRetrieveAPIView(RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = GetPackageDetailsSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):

        try:
            package = self.get_object()

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
      
      
class InstructorPackagesListAPIView(ListAPIView):
    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')
        try:
            instructor = Instructor.objects.get(user__slug=instructor_slug)
            return Package.objects.filter(instructor=instructor)
        except Instructor.DoesNotExist:
            return Package.objects.none()
    
    
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
    queryset=Package.objects.all()
    serializer_class=CourseSerializer
    permission_classes=[AllowAny]
    def get_queryset(self):
        package_slug=self.kwargs.get('slug')
        try:
            package=self.queryset.get(slug=package_slug)
            return package.courses.all()
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
    