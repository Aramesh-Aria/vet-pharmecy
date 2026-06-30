from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "status", "backend", "created_at", "paid_at")
    list_filter = ("status", "backend")
    search_fields = ("authority", "ref_id")
    readonly_fields = ("created_at",)
