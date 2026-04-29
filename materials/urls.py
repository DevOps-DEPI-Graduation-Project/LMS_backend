from django.urls import path
from .views import (
    MaterialListCreateView,
    CourseMaterialListCreateView,
    MaterialDetailView,
    MaterialDownloadView,
)

urlpatterns = [
    # Course materials
    path('courses/<slug:course_slug>/materials/', CourseMaterialListCreateView.as_view(), name='course-materials'),

    path('materials/', MaterialListCreateView.as_view(), name='materials-list'),
    path('materials/<slug:slug>/', MaterialDetailView.as_view(), name='materials-detail'),
    path('materials/<slug:slug>/download/', MaterialDownloadView.as_view(), name='materials-download'),
]