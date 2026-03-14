from django.urls import path
from .views.auth_views import ChangePasswordView, ResendOtpView, ResetPasswordView, StudentRegisterView, UserLogout,VerifyEmailView,UserLogin,ForgotPasswordView
from .views.student_views import StudentDetailView, StudentListView
from .views.instructor_views import InstructorCreateView, InstructorListView, InstructorDetailView
from .views.instructorLink_view import InstructorLinksListView, InstructorLinksCreateView, InstructorLinksUpdateView, InstructorLinksDeleteView
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
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
    ################################student urls############################    
      path('students',StudentListView.as_view(),name="all_students"),
      path('students/<slug:slug>/',StudentDetailView.as_view(),name="student_detail"),
      ################################instructor urls############################
      path('instructors/create/',InstructorCreateView.as_view(),name="create_instructor"),
     path('instructors/',InstructorListView.as_view(),name="all_instructors"),
     path('instructors/<slug:slug>/',InstructorDetailView.as_view(),name="instructor_detail"),
     #=======================================instructor Links==========================================
     path('instructors/<slug:instructor_slug>/links/', InstructorLinksListView.as_view(), name='instructor_links_list'),
     path('instructors/<slug:instructor_slug>/links/create/', InstructorLinksCreateView.as_view(), name='instructor_links_create'),
     path('instructors/links/<slug:slug>/update/', InstructorLinksUpdateView.as_view(), name='instructor_links_update'),
     path('instructors/links/<slug:slug>/delete/', InstructorLinksDeleteView.as_view(), name='instructor_links_delete'),
    
]