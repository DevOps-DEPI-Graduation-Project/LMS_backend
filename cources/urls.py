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
    path('courses/<int:id>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),
    path('courses/update/<int:id>/', CourseUpdateAPIView.as_view(), name='updateCourseById'),
    path('courses/delete/<int:id>/', CourseDeleteAPIView.as_view(), name='deleteCourseById'),
    path('instructor/<str:instructor_slug>/courses/', InstructorCoursesListAPIView.as_view(), name='listInstructorCourses'),

    # ================== Packages ==================
    path('packages/create/', PackageCreateAPIView.as_view(), name='createPackage'),
    path('packages/all/', GetAllPackagesAPIView.as_view(), name='listAllPackages'),
    path('packages/<int:id>/', PackageRetrieveAPIView.as_view(), name='getPackageById'),
    path('packages/update/<int:id>/', PackageUpdateAPIView.as_view(), name='updatePackageById'),
    path('packages/delete/<int:id>/', PackageDeleteAPIView.as_view(), name='deletePackageById'),
    path('instructor/<str:instructor_slug>/packages/', InstructorPackagesListAPIView.as_view(), name='listInstructorPackages'),
    path('packages/<int:id>/add_courses/', AddCourseToPackageAPIView.as_view(), name='addCourseToPackage'),
    path('packages/<int:id>/remove_courses/', RemoveCourseFromPackageAPIView.as_view(), name='removeCourseFromPackage'),

    # ================== Instructor Profiles ==================
    path('instructors/<str:slug>/profile/', InstructorProfileAPIView.as_view(), name='instructorProfile'),
    path('allInstructors/profiles/', AllInstructorsProfileAPIView.as_view(), name='allInstructorsProfile'),
]