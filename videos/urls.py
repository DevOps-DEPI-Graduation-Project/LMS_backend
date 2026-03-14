from django.urls import path
from .views import (
    VideosListApiView,
    VideosCreateApiView,
    VideosRetrieveApiView,
    VideosDestroyApiView,
    VideosUpdateApiView
)

urlpatterns = [
    path('videos/', VideosListApiView.as_view(), name='videos-list'),
    path('videos/create/', VideosCreateApiView.as_view(), name='videos-create'),
    path('videos/<slug:slug>/', VideosRetrieveApiView.as_view(), name='videos-retrieve'),
    path('videos/<slug:slug>/update/', VideosUpdateApiView.as_view(), name='videos-update'),
    path('videos/<slug:slug>/delete/', VideosDestroyApiView.as_view(), name='videos-delete'),
]