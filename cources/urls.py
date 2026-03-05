from django.urls import path
from .views import CourseCreateAPIView

urlpatterns = [
    path('course/create/', CourseCreateAPIView.as_view(), name='course-create'),
]