from django.urls import path
from .views import CourseCreateAPIView, CourseListAPIView, CourseRetrieveAPIView

urlpatterns = [
    path('courses/create/', CourseCreateAPIView.as_view(), name='createCourse'),
    path('courses/all/', CourseListAPIView.as_view(), name='listAllCourses'),
    path('courses/<int:id>/', CourseRetrieveAPIView.as_view(), name='getCourseById'),
]