from django.urls import path

from cources.views.courses_view import (
    AllInstructorsProfileAPIView,
    CourseCreateAPIView,
    CourseListAPIView,
    CourseRetrieveAPIView,
    CourseUpdateAPIView,
    CourseDeleteAPIView,
    InstructorProfileAPIView,
    InstructorCoursesListAPIView
)
from cources.views.packages_view import (
    GetAllPackagesAPIView,
    PackageCoursesListAPIView,
    PackageCreateAPIView,
    PackageRetrieveAPIView,
    PackageUpdateAPIView,
    PackageDeleteAPIView,
    InstructorPackagesListAPIView,
    AddCourseToPackageAPIView,
    RemoveCourseFromPackageAPIView
)

urlpatterns = [
    # ================== Courses ==================
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/<str:slug>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),
    path('courses/update/<str:slug>/', CourseUpdateAPIView.as_view(), name='updateCourseById'),
    path('courses/delete/<str:slug>/', CourseDeleteAPIView.as_view(), name='deleteCourseById'),
    path('instructor/<str:instructor_slug>/courses/', InstructorCoursesListAPIView.as_view(), name='listInstructorCourses'),

    # ================== Packages ==================
    path('packages/create/', PackageCreateAPIView.as_view(), name='createPackage'),
    path('packages/all/', GetAllPackagesAPIView.as_view(), name='listAllPackages'),
    path('packages/<str:slug>/', PackageRetrieveAPIView.as_view(), name='getPackageById'),
    path('packages/update/<str:slug>/', PackageUpdateAPIView.as_view(), name='updatePackageById'),
    path('packages/delete/<str:slug>/', PackageDeleteAPIView.as_view(), name='deletePackageById'),
    path('packages/<str:slug>/courses/',PackageCoursesListAPIView.as_view(), name='getCoursesInPackage'),
    path('instructor/<str:instructor_slug>/packages/', InstructorPackagesListAPIView.as_view(), name='listInstructorPackages'),
    path('packages/<str:slug>/add_courses/', AddCourseToPackageAPIView.as_view(), name='addCourseToPackage'),
    path('packages/<str:slug>/remove_courses/', RemoveCourseFromPackageAPIView.as_view(), name='removeCourseFromPackage'),
     
    # ================== Instructor Profiles ==================
    path('instructor/<str:instructor_slug>/profile/', InstructorProfileAPIView.as_view(), name='instructorProfile'),
    path('instructor/all/profiles/', AllInstructorsProfileAPIView.as_view(), name='allInstructorsProfile'),
]