"""Pay-at-pickup backend used at launch (ADR-0005).

No online money movement: the Payment is parked as INITIATED and Staff settle it
in person at the pharmacy, then mark it paid via :func:`settle_in_person`.
"""
from django.utils import timezone

from ..models import Payment
from .base import BasePaymentBackend, StartResult


class ManualPickupBackend(BasePaymentBackend):
    online = False

    def start(self, payment) -> StartResult:
        # Nothing to redirect to; the Owner pays when collecting the order.
        if payment.status != Payment.Status.INITIATED:
            payment.status = Payment.Status.INITIATED
            payment.save(update_fields=["status"])
        return StartResult(payment_id=payment.pk, redirect_url=None)

    def verify(self, payment, data: dict) -> bool:
        # Settlement happens in person, not via a callback. Idempotent: report
        # the current paid state without changing anything.
        return payment.is_paid


def settle_in_person(payment) -> Payment:
    """Mark a pay-at-pickup payment as collected. Idempotent."""
    if not payment.is_paid:
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at"])
    return payment
