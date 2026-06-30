"""Dummy online backend for development and tests.

Exercises the full online-payment flow (redirect → callback → verify) without a
real gateway, so the Phase-5 plumbing is testable now. NOT for production.
"""
from django.utils import timezone

from ..models import Payment
from .base import BasePaymentBackend, StartResult


class DummyOnlineBackend(BasePaymentBackend):
    online = True

    def start(self, payment) -> StartResult:
        payment.authority = f"dummy-{payment.pk}"
        payment.save(update_fields=["authority"])
        return StartResult(
            payment_id=payment.pk, redirect_url=self.get_redirect_url(payment)
        )

    def verify(self, payment, data: dict) -> bool:
        if payment.is_paid:
            return True
        if data.get("Status") != "OK":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return False
        payment.status = Payment.Status.PAID
        payment.ref_id = f"dummy-ref-{payment.pk}"
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "ref_id", "paid_at"])
        return True

    def get_redirect_url(self, payment) -> str | None:
        if not payment.authority:
            return None
        return f"/payments/dummy-gateway/?Authority={payment.authority}&Status=OK"
