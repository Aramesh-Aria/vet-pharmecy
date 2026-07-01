"""Custom User (phone identity) and the Owner profile (ADR-0004, CONTEXT.md).

Staff and Owners share one user model distinguished by ``role`` so the admin
and auth system work uniformly. Owner-specific data hangs off the user in a
1-1 :class:`OwnerProfile`.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import Province
from .managers import UserManager
from .validators import validate_phone, validate_postal_code


class User(AbstractBaseUser, PermissionsMixin):
    """A login account, identified by mobile phone number."""

    class Role(models.TextChoices):
        OWNER = "owner", _("مشتری")
        STAFF = "staff", _("همکار")

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


class PhoneOTP(models.Model):
    """A one-time code sent over SMS for phone verification or password reset
    (ADR-0004). Codes are stored hashed; validity is bounded by a short TTL and
    a max-attempts cap (both configurable via settings)."""

    class Purpose(models.TextChoices):
        REGISTER = "register", _("تأیید ثبت‌نام")
        RESET = "reset", _("بازیابی گذرواژه")

    phone = models.CharField(_("شماره موبایل"), max_length=11, db_index=True)
    code_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=10, choices=Purpose.choices)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("کد یک‌بارمصرف")
        verbose_name_plural = _("کدهای یک‌بارمصرف")
        indexes = [models.Index(fields=["phone", "purpose"])]

    def __str__(self):
        return f"OTP {self.phone} ({self.get_purpose_display()})"

    def is_usable(self) -> bool:
        from django.conf import settings

        return (
            self.consumed_at is None
            and self.attempts < settings.OTP_MAX_ATTEMPTS
            and timezone.now() < self.expires_at
        )


class OwnerProfile(models.Model):
    """Owner-specific data: contact, address, and notification preferences."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="owner_profile",
        verbose_name=_("کاربر"),
    )
    province = models.CharField(
        _("استان"), max_length=30, blank=True, choices=Province.choices
    )
    city = models.CharField(_("شهر"), max_length=80, blank=True)
    address = models.TextField(_("نشانی"), blank=True)
    postal_code = models.CharField(
        _("کد پستی"),
        max_length=10,
        blank=True,
        validators=[validate_postal_code],
        help_text=_("۱۰ رقم — برای ارسال سفارش‌ها در آینده."),
    )
    notify_by_sms = models.BooleanField(_("اطلاع‌رسانی پیامکی"), default=True)
    notify_by_email = models.BooleanField(_("اطلاع‌رسانی ایمیلی"), default=False)
    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)

    class Meta:
        verbose_name = _("پروفایل مشتری")
        verbose_name_plural = _("پروفایل‌های مشتریان")

    def __str__(self):
        return f"پروفایل {self.user}"

    @property
    def is_complete(self) -> bool:
        """Enough info to deliver to and contact the owner."""
        return bool(
            self.user.full_name
            and self.province
            and self.city
            and self.address
            and self.postal_code
        )
