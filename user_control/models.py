from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

Roles = (("admin", "admin"), ("creator", "creator"), ("sale", "sale"))


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        kwargs.setdefault("is_active", True)

        if not kwargs.get("is_staff"):
            raise ValueError("SuperUser must have is_staff=True")
        if not kwargs.get("is_superuser"):
            raise ValueError("SuperUser must have is_superuser=True")

        if not email:
            raise ValueError("Email field is required")

        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    fullname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(choices=Roles, max_length=8)
    shop_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True)

    USERNAME_FIELD = "email"
    objects = CustomUserManager()

    def __str__(self) -> str:
        return self.email

    class Meta:
        ordering = ("pk",)


class UserActivities(models.Model):
    user = models.ForeignKey(
        CustomUser, related_name="activities", null=True, on_delete=models.SET_NULL
    )
    email = models.EmailField()
    fullname = models.CharField(max_length=255)
    action = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.fullname} {self.action} on {self.created_at.strftime('%m/%d/%Y %H:%M')}"

    class Meta:
        ordering = ("-created_at",)
