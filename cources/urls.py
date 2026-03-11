from django.urls import path

from cources.views.courses_view import (
    AllInstructorsProfileAPIView,
    CourseCreateAPIView,
    CourseListAPIView,
    CourseRetrieveAPIView,
    CourseUpdateAPIView,
    CourseDeleteAPIView,
    TopRatedCoursesAPIView,
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
from cources.views.courses_rating_view import RateCourseAPIView
from cources.views.enrollment_view import EnrollCourseAPIView, MyEnrollmentsListAPIView


urlpatterns = [

    # ================== Courses (STATIC first) ==================
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/topRated/', TopRatedCoursesAPIView.as_view(), name='topRatedCourses'),

    # ================== Course Actions ==================
    path('courses/enroll/<str:slug>/', EnrollCourseAPIView.as_view(), name='enrollCourse'),
    path('courses/rate/<str:slug>/', RateCourseAPIView.as_view(), name='rateCourse'),

    # ================== Course CRUD (slug-based) ==================
    path('courses/update/<str:slug>/', CourseUpdateAPIView.as_view(), name='updateCourseById'),
    path('courses/delete/<str:slug>/', CourseDeleteAPIView.as_view(), name='deleteCourseById'),
    path('courses/<str:slug>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),

    # ================== Instructor Courses ==================
    path(
        'instructor/<str:instructor_slug>/courses/',
        InstructorCoursesListAPIView.as_view(),
        name='listInstructorCourses'
    ),

    # ================== Enrollment ==================
    path('myEnrollments/', MyEnrollmentsListAPIView.as_view(), name='myEnrollments'),

    # ================== Packages ==================
    path('packages/create/', PackageCreateAPIView.as_view(), name='createPackage'),
    path('packages/all/', GetAllPackagesAPIView.as_view(), name='listAllPackages'),
    path('packages/<str:slug>/courses/', PackageCoursesListAPIView.as_view(), name='getCoursesInPackage'),
    path('packages/<str:slug>/add_courses/', AddCourseToPackageAPIView.as_view(), name='addCourseToPackage'),
    path('packages/<str:slug>/remove_courses/', RemoveCourseFromPackageAPIView.as_view(), name='removeCourseFromPackage'),
    path('packages/update/<str:slug>/', PackageUpdateAPIView.as_view(), name='updatePackageById'),
    path('packages/delete/<str:slug>/', PackageDeleteAPIView.as_view(), name='deletePackageById'),
    path('packages/<str:slug>/', PackageRetrieveAPIView.as_view(), name='getPackageById'),

    # ================== Instructor Profiles ==================
    path('instructor/all/profiles/', AllInstructorsProfileAPIView.as_view(), name='allInstructorsProfile'),
    path(
        'instructor/<str:instructor_slug>/profile/',
        InstructorProfileAPIView.as_view(),
        name='instructorProfile'
    ),
]