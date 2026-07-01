from django.contrib import admin

from .models import ContactMessage, Practice


@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "tagline")}),
        ("تماس", {"fields": ("phone", "mobile", "email")}),
        ("نشانی", {"fields": ("province", "city", "address", "postal_code", "map_embed_url", "hours")}),
        ("محتوا", {"fields": ("about", "terms")}),
        ("شبکه‌ها و نماد", {"fields": ("instagram", "telegram", "enamad_html")}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        # Singleton: only ever one row (edit the existing one).
        return not Practice.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_handled", "created_at")
    list_filter = ("is_handled", "created_at")
    list_editable = ("is_handled",)
    search_fields = ("name", "phone", "message")
    readonly_fields = ("name", "phone", "message", "created_at")

    def has_add_permission(self, request):
        return False  # created only via the public form
