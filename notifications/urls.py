from django.urls import path

from notifications.views.announcements_view import (
    AnnouncementListCreateView,
    AnnouncementDetailView,
)
from notifications.views.notifications_view import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkAsReadView,
    NotificationMarkAllAsReadView,
)

urlpatterns = [
    path('announcements/', AnnouncementListCreateView.as_view(), name='announcement-list'),
    path('announcements/<slug:slug>/', AnnouncementDetailView.as_view(), name='announcement-detail'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<slug:slug>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/<slug:slug>/read/', NotificationMarkAsReadView.as_view(), name='notification-mark-as-read'),
    path('notifications/read-all/', NotificationMarkAllAsReadView.as_view(), name='notification-mark-all-as-read'),
]


# Endpoints

# GET    /api/announcements/
# POST   /api/announcements/
# GET    /api/announcements/<slug>/
# PATCH  /api/announcements/<slug>/
# PUT    /api/announcements/<slug>/
# DELETE /api/announcements/<slug>/

# GET    /api/notifications/
# GET    /api/notifications/<slug>/
# POST   /api/notifications/<slug>/read/
# POST   /api/notifications/read-all/