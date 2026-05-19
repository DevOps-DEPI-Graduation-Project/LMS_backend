from django.urls import path

from users.views.admin_view import AdminProfileView
from .views.auth_views import ChangePasswordView, ResendOtpView, ResetPasswordView, StudentRegisterView, UserLogout,VerifyEmailView,UserLogin,ForgotPasswordView,CheckTokenView
from .views.student_views import StudentDetailView, StudentListView
from .views.instructorLink_view import InstructorLinksListView, InstructorLinksCreateView, InstructorLinksUpdateView, InstructorLinksDeleteView
from rest_framework_simplejwt.views import TokenRefreshView
from .views.total_view import TotalAPIView,InstructorTotalsBySlugAPIView, TotalCourseDetailsAPIView
from .views.instructor_views import (
    InstructorCreateView,
    InstructorListAPIView,
    InstructorDetailView,
    InstructorUpdateView,
    InstructorDeleteView
)
urlpatterns = [
  #==============================admin urls=============================
  path('admin/<slug:slug>/profile/', AdminProfileView.as_view(), name='admin_profile'),
  #==============================auth urls=============================
    path('auth/register/', StudentRegisterView.as_view(), name='student-register'),
     path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
     path('auth/resend-otp/', ResendOtpView.as_view(), name='resend-otp'),
      path('auth/login/',UserLogin.as_view(),name='login'),
      path('auth/logout/',UserLogout.as_view(),name='logout'),
      path('auth/token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
      path('auth/forgot-password/',ForgotPasswordView.as_view(),name='forgot_password'),
      path('auth/reset-password/',ResetPasswordView.as_view(),name='reset_password'), 
      path('auth/change-password/',ChangePasswordView.as_view(),name='change_password'),
      path('auth/check-token/',CheckTokenView.as_view(),name="check_token"),
    ################################student urls############################    
      # path('admin/students',StudentListView.as_view(),name="all_students"),
    path('students/<slug:slug>/',StudentDetailView.as_view(),name="student_detail"),
      ################################instructor urls############################
    path("instructors/", InstructorListAPIView.as_view()),
    path("instructors/create/", InstructorCreateView.as_view()),
    path("instructors/<slug:slug>/", InstructorDetailView.as_view()),
    path("instructors/<slug:slug>/update/", InstructorUpdateView.as_view()),
    path("instructors/<slug:slug>/delete/", InstructorDeleteView.as_view()),
     #=======================================instructor Links==========================================
     path('instructors/<slug:instructor_slug>/links/', InstructorLinksListView.as_view(), name='instructor_links_list'),
     path('instructors/<slug:instructor_slug>/links/create/', InstructorLinksCreateView.as_view(), name='instructor_links_create'),
     path('instructors/links/<slug:slug>/update/', InstructorLinksUpdateView.as_view(), name='instructor_links_update'),
     path('instructors/links/<slug:slug>/delete/', InstructorLinksDeleteView.as_view(), name='instructor_links_delete'),
     #################################### total count===================================
     path('admin/totalFetch',TotalAPIView.as_view(),name='total_api'),
    path('instructor/<slug:slug>/totals/', InstructorTotalsBySlugAPIView.as_view(), name='instructor_totals_slug_api'),
    path('totalCourseDetails/<slug:slug>/', TotalCourseDetailsAPIView.as_view(), name='total_course_attachments_api'),

    
]