from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("user_control.urls")),
    path("api/v1/", include("app_control.urls")),
]
