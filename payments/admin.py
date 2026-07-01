from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "status", "backend", "created_at", "paid_at")
    list_filter = ("status", "backend")
    search_fields = ("authority", "ref_id")
    # All of these are set by the system / gateway, never typed by staff:
    # created_at on creation; authority/ref_id/paid_at on a successful payment
    # (settle-at-pickup or the gateway verify callback).
    readonly_fields = ("created_at", "paid_at", "authority", "ref_id", "backend")
