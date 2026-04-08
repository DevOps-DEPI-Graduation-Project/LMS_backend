"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.http import HttpResponse
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from users import permissions

def home(request):
    return HttpResponse("Welcome to LMS Backend!")

schema_view = get_schema_view(
openapi.Info(
    title="LMS API",
    default_version='v1',
    description="Simple API documentation for LMS",
),
public=True,
)

# urlpatterns = [
#     path('', home),
#     path('admin/', admin.site.urls),
#     path("api/", include("users.urls")),  
#     path('api/', include('cources.urls')),
#     path("api/", include("materials.urls")),
#     path('api/', include('notifications.urls')),
#     path('api/', include('quizzes.urls')),
#     path('api/',include("videos.urls")),

#     path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
# ]
urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),

    path("api/", include("users.urls")),
    path("api/", include("cources.urls")),
    path("api/", include("materials.urls")),
    path("api/", include("notifications.urls")),
    path("api/", include("quizzes.urls")),
    path("api/", include("videos.urls")),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
