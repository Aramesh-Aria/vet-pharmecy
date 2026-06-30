"""Custom User (phone identity) and the Owner profile (ADR-0004, CONTEXT.md).

Staff and Owners share one user model distinguished by ``role`` so the admin
and auth system work uniformly. Owner-specific data hangs off the user in a
1-1 :class:`OwnerProfile`.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager
from .validators import validate_phone


class User(AbstractBaseUser, PermissionsMixin):
    """A login account, identified by mobile phone number."""

    class Role(models.TextChoices):
        OWNER = "owner", _("مالک")
        STAFF = "staff", _("کارمند")

    phone = models.CharField(
        _("شماره موبایل"),
        max_length=11,
        unique=True,
        validators=[validate_phone],
        help_text=_("نمونه: ۰۹۱۲۳۴۵۶۷۸۹"),
    )
    email = models.EmailField(_("ایمیل"), blank=True)
    full_name = models.CharField(_("نام و نام خانوادگی"), max_length=150, blank=True)
    role = models.CharField(
        _("نقش"), max_length=10, choices=Role.choices, default=Role.OWNER
    )
    phone_verified = models.BooleanField(_("شماره تأیید شده"), default=False)

    is_active = models.BooleanField(_("فعال"), default=True)
    is_staff = models.BooleanField(
        _("دسترسی به پنل مدیریت"),
        default=False,
        help_text=_("اجازه ورود به پنل مدیریت جنگو."),
    )
    date_joined = models.DateTimeField(_("تاریخ عضویت"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []  # phone + password are prompted by default.

    class Meta:
        verbose_name = _("کاربر")
        verbose_name_plural = _("کاربران")

    def __str__(self):
        return self.full_name or self.phone

    @property
    def is_owner(self) -> bool:
        return self.role == self.Role.OWNER

    @property
    def is_practice_staff(self) -> bool:
        """Practice employee (CONTEXT.md 'Staff'), distinct from Django is_staff."""
        return self.role == self.Role.STAFF


class OwnerProfile(models.Model):
    """Owner-specific data: contact, address, and notification preferences."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owner_profile",
        verbose_name=_("کاربر"),
    )
    address = models.TextField(_("نشانی"), blank=True)
    notify_by_sms = models.BooleanField(_("اطلاع‌رسانی پیامکی"), default=True)
    notify_by_email = models.BooleanField(_("اطلاع‌رسانی ایمیلی"), default=False)
    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)

    class Meta:
        verbose_name = _("پروفایل مالک")
        verbose_name_plural = _("پروفایل‌های مالکان")

    def __str__(self):
        return f"پروفایل {self.user}"
