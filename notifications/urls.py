from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet, NotificationViewSet


router = DefaultRouter()

router.register(
    r'announcements',
    AnnouncementViewSet,
    basename='announcement'
)

router.register(
    r'notifications',
    NotificationViewSet,
    basename='notification'
)


urlpatterns = [
    path('', include(router.urls)),
]


# Endpoints

# GET    /api/announcements/
# POST   /api/announcements/
# GET    /api/announcements/<slug>/

# GET    /api/notifications/
# GET    /api/notifications/<slug>/

# POST   /api/notifications/<slug>/read/
# POST   /api/notifications/read-all/