"""
URL configuration for apiMission project.
"""

from django.contrib import admin
from django.urls import include, path

from apiMission.views import api_root

urlpatterns = [
    path("", api_root, name="root"),
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api-root"),
    path("api/auth/", include("apps.users.urls")),
]
