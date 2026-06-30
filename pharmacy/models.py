"""Store models: Cart/Order (the purchase flow) and Prescription/RefillRequest
(the controlled-medication flow). See CONTEXT.md and ADR-0005.

Money is integer Rial throughout (the settlement currency). Online payment is
not live at launch; Orders and approved Refills are settled at pickup.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# Cart — the pre-checkout draft (CONTEXT.md). One per Owner.
# ---------------------------------------------------------------------------
class Cart(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name=_("مالک"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("سبد خرید")
        verbose_name_plural = _("سبدهای خرید")

    def __str__(self):
        return f"سبد {self.owner}"

    @property
    def total(self) -> int:
        return sum(item.line_total for item in self.items.all())

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, verbose_name=_("کالا")
    )
    quantity = models.PositiveIntegerField(_("تعداد"), default=1)

    class Meta:
        verbose_name = _("قلم سبد")
        verbose_name_plural = _("اقلام سبد")
        constraints = [
            models.UniqueConstraint(fields=["cart", "product"], name="uniq_cart_product")
        ]

    def __str__(self):
        return f"{self.product} ×{self.quantity}"

    @property
    def line_total(self) -> int:
        return self.product.price * self.quantity


# ---------------------------------------------------------------------------
# Order — a placed purchase, collected at the pharmacy (CONTEXT.md).
# ---------------------------------------------------------------------------
class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", _("ثبت‌شده")
        APPROVED = "approved", _("تأییدشده")
        READY = "ready", _("آمادهٔ تحویل")
        COLLECTED = "collected", _("تحویل‌شده")
        CANCELLED = "cancelled", _("لغوشده")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("مالک"),
    )
    status = models.CharField(
        _("وضعیت"), max_length=12, choices=Status.choices, default=Status.PLACED
    )
    note = models.TextField(_("یادداشت مشتری"), blank=True)
    staff_note = models.TextField(_("یادداشت کارمند"), blank=True)
    created_at = models.DateTimeField(_("ثبت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    class Meta:
        verbose_name = _("سفارش")
        verbose_name_plural = _("سفارش‌ها")
        ordering = ["-created_at"]

    def __str__(self):
        return f"سفارش #{self.pk}"

    @property
    def total(self) -> int:
        return sum(item.line_total for item in self.items.all())

    def get_absolute_url(self):
        return reverse("pharmacy:order_detail", kwargs={"pk": self.pk})


class OrderItem(models.Model):
    """A line in an Order. Name and price are snapshotted at purchase so later
    catalog edits never rewrite order history."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, blank=True
    )
    product_name = models.CharField(_("نام کالا"), max_length=200)
    unit_price = models.PositiveBigIntegerField(_("قیمت واحد (ریال)"))
    quantity = models.PositiveIntegerField(_("تعداد"))

    class Meta:
        verbose_name = _("قلم سفارش")
        verbose_name_plural = _("اقلام سفارش")

    def __str__(self):
        return f"{self.product_name} ×{self.quantity}"

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity


# ---------------------------------------------------------------------------
# Prescription & RefillRequest — controlled-medication flow (CONTEXT.md).
# ---------------------------------------------------------------------------
class Prescription(models.Model):
    """An authorisation, issued by a Veterinarian for a specific Animal, to
    dispense a prescription-only Medication. Created by Staff, not Owners."""

    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        related_name="prescriptions",
        verbose_name=_("حیوان"),
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="prescriptions",
        verbose_name=_("داروی نسخه‌ای"),
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_prescriptions",
        verbose_name=_("صادرکننده"),
    )
    dosage = models.CharField(_("دستور مصرف"), max_length=255, blank=True)
    notes = models.TextField(_("توضیحات"), blank=True)
    refills_allowed = models.PositiveSmallIntegerField(_("تعداد تکرار مجاز"), default=0)
    issued_at = models.DateTimeField(_("تاریخ صدور"), auto_now_add=True)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("نسخه")
        verbose_name_plural = _("نسخه‌ها")
        ordering = ["-issued_at"]

    def __str__(self):
        return f"نسخهٔ {self.product} برای {self.animal}"

    def clean(self):
        if self.product_id and not self.product.is_prescription_only:
            raise ValidationError(
                {"product": _("نسخه فقط برای داروی «فقط با نسخه» صادر می‌شود.")}
            )

    @property
    def owner(self):
        return self.animal.owner


class RefillRequest(models.Model):
    """An Owner's request to have an existing Prescription dispensed again.
    Staff approve & price it before it becomes payable (approve-then-pay,
    ADR-0005)."""

    class Status(models.TextChoices):
        REQUESTED = "requested", _("درخواست‌شده")
        APPROVED = "approved", _("تأییدشده")
        DECLINED = "declined", _("ردشده")
        READY = "ready", _("آمادهٔ تحویل")
        COLLECTED = "collected", _("تحویل‌شده")
        CANCELLED = "cancelled", _("لغوشده")

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.PROTECT,
        related_name="refill_requests",
        verbose_name=_("نسخه"),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="refill_requests",
        verbose_name=_("مالک"),
    )
    quantity = models.PositiveIntegerField(_("تعداد"), default=1)
    status = models.CharField(
        _("وضعیت"), max_length=12, choices=Status.choices, default=Status.REQUESTED
    )
    price = models.PositiveBigIntegerField(_("قیمت (ریال)"), null=True, blank=True)
    staff_note = models.TextField(_("یادداشت کارمند"), blank=True)
    created_at = models.DateTimeField(_("ثبت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    class Meta:
        verbose_name = _("درخواست تکرار نسخه")
        verbose_name_plural = _("درخواست‌های تکرار نسخه")
        ordering = ["-created_at"]

    def __str__(self):
        return f"تکرار نسخه #{self.pk}"

    def get_absolute_url(self):
        return reverse("pharmacy:refill_detail", kwargs={"pk": self.pk})
