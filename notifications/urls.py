from django.urls import path
from .views import AnnouncementCreateView, NotificationListView, MarkAsReadView

urlpatterns = [
    path("announcements/create/", AnnouncementCreateView.as_view()),
    path("notifications/", NotificationListView.as_view()),
    path("notifications/<int:pk>/read/", MarkAsReadView.as_view()),
]