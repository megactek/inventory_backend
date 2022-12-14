from django.urls import path, include
from .views import (
    CreateUserView,
    LoginView,
    MeView,
    UpdatePasswordView,
    UserActivitiesView,
    UsersView,
)
from rest_framework.routers import DefaultRouter


router = DefaultRouter(trailing_slash=False)
router.register("create_user", CreateUserView, "create_user")
router.register("login", LoginView, "login")
router.register("profile", MeView, "profile")
router.register("update_password", UpdatePasswordView, "update_password")
router.register("users", UsersView, "users")
router.register("activities", UserActivitiesView, "activities")

urlpatterns = [path("user/", include(router.urls))]
