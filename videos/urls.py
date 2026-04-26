from django.urls import path
from .views.videos_view import (
    VideosListApiView,
    VideosCreateApiView,
    VideosRetrieveApiView,
    VideosDestroyApiView,
    VideosUpdateApiView,
    CourseVideosListApiView,
)
from .views.videoprogress_view import VideoCompleteAPIView

urlpatterns = [
    path('videos/', VideosListApiView.as_view(), name='videos-list'),
    path('videos/create/', VideosCreateApiView.as_view(), name='videos-create'),
    path('videos/<slug:slug>/', VideosRetrieveApiView.as_view(), name='videos-retrieve'),
    path('videos/<slug:slug>/update/', VideosUpdateApiView.as_view(), name='videos-update'),
    path('videos/<slug:slug>/delete/', VideosDestroyApiView.as_view(), name='videos-delete'),
    path('courses/<slug:course_slug>/videos/', CourseVideosListApiView.as_view(), name='course-videos'),
    path('video-complete/<slug:video_slug>/', VideoCompleteAPIView.as_view(), name='video-complete'),

]