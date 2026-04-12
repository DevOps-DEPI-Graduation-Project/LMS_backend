from django.urls import path
from .views import (
    MaterialListCreateView,
    MaterialDetailView,
    MaterialDownloadView,
)

urlpatterns = [
    path('materials/', MaterialListCreateView.as_view(), name='materials-list'),
    path('materials/<slug:slug>/', MaterialDetailView.as_view(), name='materials-detail'),
    path('materials/<slug:slug>/download/', MaterialDownloadView.as_view(), name='materials-download'),
]