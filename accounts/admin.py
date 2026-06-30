from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import OwnerProfile, PhoneOTP, User


class OwnerProfileInline(admin.StackedInline):
    model = OwnerProfile
    can_delete = False
    extra = 0
    verbose_name_plural = _("پروفایل مالک")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreationForm
    form = UserAdminChangeForm
    model = User
    inlines = [OwnerProfileInline]

    list_display = ("phone", "full_name", "role", "phone_verified", "is_active")
    list_filter = ("role", "phone_verified", "is_active", "is_staff")
    search_fields = ("phone", "full_name", "email")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("اطلاعات شخصی"), {"fields": ("full_name", "email")}),
        (_("نقش و وضعیت"), {"fields": ("role", "phone_verified")}),
        (
            _("دسترسی‌ها"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("تاریخ‌ها"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "email", "role",
                           "password1", "password2"),
            },
        ),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone", "purpose", "attempts", "created_at", "expires_at", "consumed_at")
    list_filter = ("purpose",)
    search_fields = ("phone",)
    readonly_fields = ("phone", "code_hash", "purpose", "attempts", "created_at",
                       "expires_at", "consumed_at")
