"""User manager keyed on phone number (ADR-0004)."""
from django.contrib.auth.base_user import BaseUserManager

from .validators import normalize_phone


class UserManager(BaseUserManager):
    """Create users identified by phone instead of username."""

    use_in_migrations = True

    def _create_user(self, phone, password, **extra_fields):
        if not phone:
            raise ValueError("شماره موبایل لازم است.")
        phone = normalize_phone(phone)
        email = extra_fields.pop("email", "")
        if email:
            email = self.normalize_email(email)
        user = self.model(phone=phone, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", self.model.Role.OWNER)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", self.model.Role.STAFF)
        extra_fields.setdefault("phone_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(phone, password, **extra_fields)
