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
    InstructorCoursesListAPIView,
    CourseStudentsAPIView
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
    RemoveCourseFromPackageAPIView,
    EnrollPackageAPIView,
)
from cources.views.courses_rating_view import RateCourseAPIView
# from cources.views.enrollment_view import EnrollCourseAPIView, InstructorEnrollmentsAPIView , MyEnrollmentsListAPIView,AdminEnrollmentsAPIView
from cources.views.enrollment_view import EnrollCourseAPIView, MyEnrollmentsListAPIView ,AdminStudentsAPIView, InstructorStudentsAPIView,AdminStudentDetailsAPIView,ToggleStudentStatusAPIView,DeleteStudentAPIView,InstructorStudentDetailsAPIView,InstructorStudentSummaryAPIView

urlpatterns = [
    path("admin/students/",AdminStudentsAPIView.as_view(),name="adminStudents"), # done
    path("courses/myEnrollments/", MyEnrollmentsListAPIView.as_view(), name="myEnrollments"),
    path("admin/students/<str:student_slug>/details/",AdminStudentDetailsAPIView.as_view(), name="adminStudentDetails"), #done
    path("admin/students/<str:student_slug>/status/",ToggleStudentStatusAPIView.as_view(), name="toggleStudentStatus"),  #done
    path("admin/students/<str:student_slug>/delete/", DeleteStudentAPIView.as_view(),name="deleteStudent"),   #done
    # ================== Courses ==================
    path('courses/topRated/',TopRatedCoursesAPIView.as_view(),name='topRatedCourses'),
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/<str:slug>/', CourseRetrieveAPIView.as_view(), name='getCourseBySlug'),
    path('courses/<str:course_slug>/students/', CourseStudentsAPIView.as_view(), name='getStudentsByCourseSlug'),
    # ================== Rating ====================
    path('courses/rate/<str:slug>/', RateCourseAPIView.as_view(),name='RateCourses'), 
    # GET /api/courses/topRated/?limit=5
    path('courses/update/<str:slug>/', CourseUpdateAPIView.as_view(), name='updateCourseBySlug'),
    path('courses/delete/<str:slug>/', CourseDeleteAPIView.as_view(), name='deleteCourseBySlug'),
    #  path('instructor/<str:instructor_slug>/courses/', InstructorCoursesListAPIView.as_view(), name='listInstructorCourses'),
    # ================ enrollment ==================
    path('courses/enroll/<str:slug>/', EnrollCourseAPIView.as_view(),name='enrollCourse'),
    # ================== Packages ==================
    path('packages/create/', PackageCreateAPIView.as_view(), name='createPackage'),
    path('packages/all/', GetAllPackagesAPIView.as_view(), name='listAllPackages'),
    path('packages/<str:slug>/', PackageRetrieveAPIView.as_view(), name='getPackageBySlug'),
    path('packages/update/<str:slug>/', PackageUpdateAPIView.as_view(), name='updatePackageBySlug'),
    path('packages/delete/<str:slug>/', PackageDeleteAPIView.as_view(), name='deletePackageBySlug'), 
    path('packages/enroll/<str:package_slug>/',EnrollPackageAPIView.as_view(),name="enrollPackage"),
    path('packages/<str:slug>/courses/',PackageCoursesListAPIView.as_view(), name='getCoursesInPackage'),
    path('instructor/<str:instructor_slug>/packages/', InstructorPackagesListAPIView.as_view(), name='listInstructorPackages'),
    path('packages/<str:slug>/add_courses/', AddCourseToPackageAPIView.as_view(), name='addCourseToPackage'),
    path('packages/<str:slug>/remove_courses/', RemoveCourseFromPackageAPIView.as_view(), name='removeCourseFromPackage'),
    # ================== Instructor Profiles ==================
    path('instructor/<str:instructor_slug>/courses/', InstructorCoursesListAPIView.as_view(), name='instructorProfile'),##done
    path('instructor/<str:instructor_slug>/profile/', InstructorProfileAPIView.as_view(), name='instructorProfile'),
    # path('instructor/all/profiles/', AllInstructorsProfileAPIView.as_view(), name='allInstructorsProfile'), 
    path("instructor/<str:instructor_slug>/students/", InstructorStudentsAPIView.as_view(),name="instructorStudents"), #done
    path("instructor/courses/<slug:course_slug>/students/<slug:student_slug>/",InstructorStudentDetailsAPIView.as_view(),name="instructorStudentDetails"), #done
    path("instructor/students/<student_slug>/summary/",InstructorStudentSummaryAPIView.as_view(),name="InstructorStudentSummaryAPIView") #done
]