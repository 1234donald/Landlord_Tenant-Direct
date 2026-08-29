from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for the platform.

    Users identify and authenticate with their email address. Each user is
    assigned exactly one of the three role-based authorisation roles:
    TENANT, LANDLORD or ADMIN. Administrator accounts are created
    administratively, never through public registration.
    """

    class Role(models.TextChoices):
        TENANT = "TENANT", "Tenant"
        LANDLORD = "LANDLORD", "Landlord"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TENANT,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.email

    @property
    def is_tenant(self):
        return self.role == self.Role.TENANT

    @property
    def is_landlord(self):
        return self.role == self.Role.LANDLORD

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.full_name
