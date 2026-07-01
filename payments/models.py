"""Payment model (ADR-0005).

A Payment links to a *payable* (an Order or an Online Visit) via a generic
relation, so the payments app does not depend on apps that ship in later phases.
Online payment is inactive until e-Namad + a real gateway are in place; at launch
the manual pay-at-pickup backend is used.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", _("آغازشده")
        PAID = "paid", _("پرداخت‌شده")
        FAILED = "failed", _("ناموفق")
        REFUNDED = "refunded", _("بازگشت‌داده‌شده")

    # The payable object (Order / Online Visit). Generic so we avoid hard deps.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    payable = GenericForeignKey("content_type", "object_id")

    # Amount stored as integer Rial (settlement currency, ADR-0005).
    amount = models.PositiveBigIntegerField(_("مبلغ (ریال)"))
    status = models.CharField(
        _("وضعیت"), max_length=12, choices=Status.choices, default=Status.INITIATED
    )

    # Which backend processed this payment (dotted path), and gateway handles.
    backend = models.CharField(_("درگاه"), max_length=255)
    authority = models.CharField(_("شناسهٔ مرجع درگاه"), max_length=255, blank=True)
    ref_id = models.CharField(_("کد پیگیری"), max_length=255, blank=True)

    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)
    paid_at = models.DateTimeField(
        _("زمان پرداخت"),
        null=True,
        blank=True,
        help_text=_("به‌صورت خودکار هنگام موفقیت پرداخت ثبت می‌شود."),
    )

    class Meta:
        verbose_name = _("پرداخت")
        verbose_name_plural = _("پرداخت‌ها")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["authority"]),
        ]

    def __str__(self):
        return f"پرداخت #{self.pk} ({self.get_status_display()})"

    @property
    def is_paid(self) -> bool:
        return self.status == self.Status.PAID
