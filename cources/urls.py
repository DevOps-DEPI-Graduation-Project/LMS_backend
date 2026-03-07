from django.urls import path

from cources.views.courses_view import InstructorCoursesListAPIView, CourseCreateAPIView, CourseListAPIView, CourseRetrieveAPIView, CourseUpdateAPIView, CourseDeleteAPIView
from cources.views.packages_view import GetAllPackagesAPIView, InstructorPackagesListAPIView, PackageCreateAPIView, PackageRetrieveAPIView, PackageUpdateAPIView, PackageDeleteAPIView

urlpatterns = [
    #================== Create Course ===================
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/<int:id>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),
    path('courses/update/<int:id>/', CourseUpdateAPIView.as_view(), name='updateCourseById'),
    path('courses/delete/<int:id>/', CourseDeleteAPIView.as_view(), name='deleteCourseById'),
    path('instructor/<str:instructor_slug>/courses/', InstructorCoursesListAPIView.as_view(), name='listInstructorCourses'),
    #=================== Create Package ===================
    path('packages/create/', PackageCreateAPIView.as_view(), name='createPackage'),
    path('packages/all/', GetAllPackagesAPIView.as_view(), name='listAllPackages'),
    path('packages/<int:id>/', PackageRetrieveAPIView.as_view(), name='getPackageById'),
    path('packages/update/<int:id>/', PackageUpdateAPIView.as_view(), name='updatePackageById'),
    path('packages/delete/<int:id>/', PackageDeleteAPIView.as_view(), name='deletePackageById'),
    path('instructor/<str:instructor_slug>/packages/', InstructorPackagesListAPIView.as_view(), name='listInstructorPackages'),
    ##=================== Update course in package ===================
    path('packages/<int:package_id>/update_course/<int:course_id>/', PackageUpdateAPIView.as_view(), name='updateCourseInPackage'),
    path('packages/<int:package_id>/remove_course/<int:course_id>/', PackageUpdateAPIView.as_view(), name='removeCourseFromPackage'),
]