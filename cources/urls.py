from django.urls import path
from .views import CourseCreateAPIView, CourseListAPIView, CourseRetrieveAPIView,CourseUpdateAPIView,CourseDeleteAPIView

urlpatterns = [
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/<int:id>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),
    path('courses/update/<int:id>/', CourseUpdateAPIView.as_view(), name='updateCourseById'),
    path('courses/delete/<int:id>/', CourseDeleteAPIView.as_view(), name='deleteCourseById'),
]