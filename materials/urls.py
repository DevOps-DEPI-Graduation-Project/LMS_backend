from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialViewSet


# Router automatically generates CRUD endpoints
router = DefaultRouter()

router.register("materials", MaterialViewSet, basename="materials")


urlpatterns = [
    path("", include(router.urls)),
]