from django.contrib import admin

from . import services
from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Prescription,
    RefillRequest,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "status", "total_display", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__phone", "owner__full_name", "id")
    autocomplete_fields = ("owner",)
    inlines = [OrderItemInline]
    actions = ("approve", "mark_ready", "mark_collected", "cancel")

    @admin.display(description="مبلغ کل (ریال)")
    def total_display(self, obj):
        return obj.total

    def _transition(self, request, queryset, status, label):
        for order in queryset:
            services.set_order_status(order, status)
        self.message_user(request, f"{queryset.count()} سفارش به «{label}» تغییر کرد.")

    @admin.action(description="تأیید سفارش‌ها")
    def approve(self, request, queryset):
        self._transition(request, queryset, Order.Status.APPROVED, "تأییدشده")

    @admin.action(description="آماده تحویل")
    def mark_ready(self, request, queryset):
        self._transition(request, queryset, Order.Status.READY, "آمادهٔ تحویل")

    @admin.action(description="تحویل‌شده (تسویه هنگام تحویل)")
    def mark_collected(self, request, queryset):
        self._transition(request, queryset, Order.Status.COLLECTED, "تحویل‌شده")

    @admin.action(description="لغو سفارش‌ها (بازگردانی موجودی)")
    def cancel(self, request, queryset):
        self._transition(request, queryset, Order.Status.CANCELLED, "لغوشده")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "animal", "product", "issued_by", "issued_at", "is_active")
    list_filter = ("is_active", "issued_at")
    search_fields = ("animal__name", "product__name", "animal__owner__phone")
    autocomplete_fields = ("animal", "product")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("animal", "product")

    def save_model(self, request, obj, form, change):
        if not obj.issued_by_id:
            obj.issued_by = request.user  # the issuing vet/staff
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            from catalog.models import Product

            kwargs["queryset"] = Product.objects.filter(is_prescription_only=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RefillRequest)
class RefillRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "prescription", "status", "price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__phone", "owner__full_name", "id")
    autocomplete_fields = ("prescription", "owner")

    def save_model(self, request, obj, form, change):
        # Route status/price edits through the service so payment + notifications
        # fire (approve-then-pay; settle at collection).
        if change and ("status" in form.changed_data or "price" in form.changed_data):
            services.set_refill_status(obj, obj.status, price=obj.price)
        else:
            super().save_model(request, obj, form, change)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "item_count")
    search_fields = ("owner__phone",)
    inlines = [CartItemInline]
