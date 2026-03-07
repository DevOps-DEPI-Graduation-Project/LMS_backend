
# from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated, AllowAny
# from .models import Course, Package
# from .serializer import CourseCreateSerializer, CourseSerializer, GetAllPackagesSerializer, PackageCreateSerializer
# from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin, IsPackageOwnerOrAdmin
# from utils.apiResponse import success_response, error_response


# # =================== Create Course ===================
# class CourseCreateAPIView(CreateAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseCreateSerializer
#     permission_classes = [IsInstructorOrAdmin]

#     def create(self, request, *args, **kwargs):

#         serializer = self.get_serializer(data=request.data)

#         if not serializer.is_valid():
#             return error_response(
#                 message="Invalid course data",
#                 errors=serializer.errors,
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         serializer.save(instructor=request.user.instructor_profile)

#         return success_response(
#             message="Course created successfully",
#             data=serializer.data,
#             status_code=status.HTTP_201_CREATED
#         )


# # =================== List All Courses ===================
# class CourseListAPIView(ListAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseSerializer
#     permission_classes = [AllowAny]

#     def list(self, request, *args, **kwargs):

#         courses = self.get_queryset()

#         if not courses.exists():
#             return success_response(
#                 message="No courses available",
#                 data=[]
#             )

#         serializer = self.get_serializer(courses, many=True)

#         return success_response(
#             message="Courses retrieved successfully",
#             data=serializer.data
#         )


# # =================== Retrieve Course by ID ===================
# class CourseRetrieveAPIView(RetrieveAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseSerializer
#     permission_classes = [AllowAny]
#     lookup_field = "id"

#     def retrieve(self, request, *args, **kwargs):

#         try:
#             course = self.get_object()

#         except Exception:
#             return error_response(
#                 message="Course not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = self.get_serializer(course)

#         return success_response(
#             message="Course retrieved successfully",
#             data=serializer.data
#         )


# # =================== Update Course ===================
# class CourseUpdateAPIView(UpdateAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseCreateSerializer
#     permission_classes = [IsAuthenticated, IsCourseOwnerOrAdmin]
#     lookup_field = "id"

#     def update(self, request, *args, **kwargs):

#         try:
#             course = self.get_object()

#         except Exception:
#             return error_response(
#                 message="Course not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = self.get_serializer(
#             course,
#             data=request.data,
#             partial=True
#         )

#         if not serializer.is_valid():
#             return error_response(
#                 message="Invalid course data",
#                 errors=serializer.errors,
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         serializer.save()

#         return success_response(
#             message="Course updated successfully",
#             data=serializer.data
#         )
        
# # =================== Delete Course ===================
# class CourseDeleteAPIView(DestroyAPIView):
#     queryset = Course.objects.all()
#     serializer_class = CourseSerializer
#     permission_classes = [IsAuthenticated, IsCourseOwnerOrAdmin]
#     # permission_classes = [AllowAny]
    
#     lookup_field = "id"

#     def destroy(self, request, *args, **kwargs):
#         try:
#             course = self.get_object()
#         except Exception:
#             return error_response(
#                 message="Course not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         course.delete()
#         return success_response(
#             message="Course deleted successfully",
#             data=None
#         )
        
#       #=================== List Courses by Instructor ===================  
# class InstructorCoursesListAPIView(ListAPIView):
#     queryset=Course.objects.all()
#     serializer_class=CourseSerializer
#     permission_classes=[AllowAny]
#     def get_queryset(self):
#         instructor_id=self.kwargs.get('instructor_id')
#         return self.queryset.filter(instructor__id=instructor_id)
        
        
# #===================get all packages===================

# class GetAllPackagesAPIView(ListAPIView):
#     queryset = Package.objects.all()
#     serializer_class = GetAllPackagesSerializer
#     permission_classes = [AllowAny]
    
#     def list(self, request, *args, **kwargs):

#         packages = self.get_queryset()

#         if not packages.exists():
#             return success_response(
#                 message="No packages available",
#                 data=[]
#             )

#         serializer = self.get_serializer(packages, many=True)

#         return success_response(
#             message="Packages retrieved successfully",
#             data=serializer.data
#         )
        
# #=================== Create Package ===================
# class PackageCreateAPIView(CreateAPIView):
#     queryset=Package.objects.all()
#     serializer_class=PackageCreateSerializer
#     permission_classes=[IsInstructorOrAdmin]
#     def create(self,request, *args, **kwargs):
#         serializer=self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             return error_response(
#                 message="Invalid package data",
#                 errors=serializer.errors,
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )
#         serializer.save(instructor=request.user.instructor_profile)
#         return success_response(
#             message="Package created successfully",
#             data=serializer.data,
#             status_code=status.HTTP_201_CREATED
#         )
        
# #===================get package by id===================
# class PackageRetrieveAPIView(RetrieveAPIView):
#     queryset = Package.objects.all()
#     serializer_class = GetAllPackagesSerializer
#     permission_classes = [AllowAny]
#     lookup_field = "id"

#     def retrieve(self, request, *args, **kwargs):

#         try:
#             package = self.get_object()

#         except Exception:
#             return error_response(
#                 message="Package not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         serializer = self.get_serializer(package)

#         return success_response(
#             message="Package retrieved successfully",
#             data=serializer.data
#         )
        
# ##=================== Update Package ===================

# class PackageUpdateAPIView(UpdateAPIView):
#     queryset=Package.objects.all()
#     serializer_class=PackageCreateSerializer
#     permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
#     lookup_field = "id"
#     def update(self, request, *args, **kwargs):
#         try:
#             package=self.get_object()
#         except Exception:
#             return error_response(
#                 message="Package not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )
#         serializer=self.get_serializer(
#             package, data=request.data, partial=True
#         )
#         if not serializer.is_valid():
#             return error_response(
#                 message="Invalid package data",
#                 errors=serializer.errors,
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )
#         serializer.save()
#         return success_response(
#             message="Package updated successfully",
#             data=serializer.data
#         )
        
        
# #=================== Delete Package ===================
# class PackageDeleteAPIView(DestroyAPIView):
#     queryset=Package.objects.all()
#     serializer_class=GetAllPackagesSerializer
#     permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
#     lookup_field = "id"
#     def destroy(self, request, *args, **kwargs):
#       try:
#           package=self.get_object()
#       except Exception:
#           return error_response(
#               message="Package not found",
#               status_code=status.HTTP_404_NOT_FOUND
#              )  
#       package.delete()
#       return success_response(
#             message="Package deleted successfully",
#             data=None
#         )
      
      
# #===================List Packages by Instructor===================
# class InstructorPackagesListAPIView(ListAPIView):
#     queryset=Package.objects.all()
#     serializer_class=GetAllPackagesSerializer
#     permission_classes=[AllowAny]
#     def get_queryset(self):
#         instructor_id=self.kwargs.get('instructor_id')
#         return self.queryset.filter(instructor__id=instructor_id)
    
    
# #====================add course to package===================
# class AddCourseToPackageAPIView(UpdateAPIView):
#     queryset=Package.objects.all()
#     serializer_class=PackageCreateSerializer
#     permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
#     lookup_field = "id"
#     def update(self, request, *args, **kwargs):

#         try:
#             package = self.get_object()
#         except Exception:
#             return error_response(
#                 message="Package not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         course_ids = request.data.get('course_ids', [])
        

#         courses = Course.objects.filter(id__in=course_ids, instructor=package.instructor)

#         if not courses.exists():
#             return error_response(
#                 message="No valid courses found",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         package.courses.add(*courses)

#         return success_response(
#             message="Courses added to package successfully"
#         )
        
# ##===================get courses in package===================
# class PackageCoursesListAPIView(ListAPIView):
#     queryset=Package.objects.all()
#     serializer_class=CourseSerializer
#     permission_classes=[AllowAny]
#     def get_queryset(self):
#         package_id=self.kwargs.get('package_id')
#         try:
#             package=self.queryset.get(id=package_id)
#             return package.courses.all()
#         except Package.DoesNotExist:
#             return Course.objects.none()
        
        
# #=================== Remove Course from Package ===================
# class RemoveCourseFromPackageAPIView(UpdateAPIView):
#     queryset=Package.objects.all()
#     serializer_class=PackageCreateSerializer
#     permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
#     lookup_field = "id"
#     def update(self, request, *args, **kwargs):

#         try:
#             package = self.get_object()
#         except Exception:
#             return error_response(
#                 message="Package not found",
#                 status_code=status.HTTP_404_NOT_FOUND
#             )

#         course_ids = request.data.get('course_ids', [])

#         courses = Course.objects.filter(id__in=course_ids, instructor=package.instructor)

#         if not courses.exists():
#             return error_response(
#                 message="No valid courses found",
#                 status_code=status.HTTP_400_BAD_REQUEST
#             )

#         package.courses.remove(*courses)

#         return success_response(
#             message="Courses removed from package successfully",
#         )
    
