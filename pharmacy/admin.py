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
    list_display = (
        "id", "animal", "product", "quantity", "remaining", "issued_by",
        "issued_at", "is_active",
    )
    list_filter = ("is_active", "issued_at")
    search_fields = ("animal__name", "product__name", "animal__owner__phone")

    @admin.display(description="باقی‌مانده")
    def remaining(self, obj):
        return obj.remaining_quantity
    # `animal` stays autocomplete (owners may have many). `product` is a plain
    # filtered <select>: a prescription is only valid for a «فقط با نسخه» medication,
    # so the dropdown must show *only* those — an autocomplete loads its options from
    # the Product autocomplete endpoint, which ignores this filter and would let staff
    # pick an ineligible product, then fail validation with a confusing error.
    autocomplete_fields = ("animal",)

    class Media:
        # Filters the medication dropdown to the selected pet's category.
        js = ["js/admin_prescription.js"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("animal", "product")

    def save_model(self, request, obj, form, change):
        if not obj.issued_by_id:
            obj.issued_by = request.user  # the issuing vet/staff
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            from catalog.models import Product

            from core.widgets import CategoryDataSelect

            qs = Product.objects.filter(is_prescription_only=True).select_related(
                "animal_category"
            )
            kwargs["queryset"] = qs
            field = super().formfield_for_foreignkey(db_field, request, **kwargs)
            # Tag each option with its category so the JS can hide non-matching
            # medications once the pet is chosen. Validation still enforces it.
            field.widget = CategoryDataSelect(
                category_by_value={p.pk: p.animal_category_id for p in qs}
            )
            field.widget.choices = field.choices
            return field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RefillRequest)
class RefillRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "prescription", "quantity", "status",
                    "allowance_granted", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("owner__phone", "owner__full_name", "id")
    autocomplete_fields = ("prescription", "owner")
    readonly_fields = ("allowance_granted", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # Route status changes through the service: approving grants the quantity
        # to the prescription allowance (the Owner then orders via the cart).
        if change and "status" in form.changed_data:
            services.set_refill_status(obj, obj.status)
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
