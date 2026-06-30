"""Zarinpal payment backend (ADR-0005, Phase 5).

Implements the gateway round trip behind the standard backend interface:
``start`` requests an authority and sends the Owner to the gateway; ``verify``
confirms the result on callback (idempotent). Uses the stdlib so no extra
dependency.

Gated by ``PAYMENTS_ONLINE_ENABLED`` and inactive until a real merchant id is
configured — sandbox by default. Amounts are sent in Rial (our stored unit);
flip the conversion if the contracted gateway expects Toman.

NOTE: cannot be exercised end-to-end without merchant credentials + a live site
(the e-Namad dependency). Verify against the gateway sandbox before Phase 5.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.urls import reverse

from ..models import Payment
from .base import BasePaymentBackend, StartResult

TIMEOUT = 15


def _bases():
    if getattr(settings, "ZARINPAL_SANDBOX", True):
        return (
            "https://sandbox.zarinpal.com/pg/v4/payment/request.json",
            "https://sandbox.zarinpal.com/pg/v4/payment/verify.json",
            "https://sandbox.zarinpal.com/pg/StartPay/",
        )
    return (
        "https://payment.zarinpal.com/pg/v4/payment/request.json",
        "https://payment.zarinpal.com/pg/v4/payment/verify.json",
        "https://payment.zarinpal.com/pg/StartPay/",
    )


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


class ZarinpalBackend(BasePaymentBackend):
    online = True

    def start(self, payment) -> StartResult:
        request_url, _, startpay = _bases()
        callback = settings.SITE_BASE_URL.rstrip("/") + reverse("payments:callback")
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": payment.amount,
            "callback_url": callback,
            "description": f"پرداخت #{payment.pk}",
        }
        try:
            result = _post(request_url, payload)
        except (urllib.error.URLError, OSError, ValueError):
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return StartResult(payment_id=payment.pk, redirect_url=None)

        data = result.get("data") or {}
        if data.get("code") == 100 and data.get("authority"):
            payment.authority = data["authority"]
            payment.save(update_fields=["authority"])
            return StartResult(payment_id=payment.pk, redirect_url=startpay + data["authority"])

        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        return StartResult(payment_id=payment.pk, redirect_url=None)

    def verify(self, payment, data: dict) -> bool:
        if payment.is_paid:
            return True  # idempotent
        if data.get("Status") != "OK":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])
            return False

        _, verify_url, _ = _bases()
        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": payment.amount,
            "authority": payment.authority,
        }
        try:
            result = _post(verify_url, payload)
        except (urllib.error.URLError, OSError, ValueError):
            return False

        verified = result.get("data") or {}
        # 100 = paid; 101 = already verified (treat as success, idempotent).
        if verified.get("code") in (100, 101):
            from django.utils import timezone

            payment.status = Payment.Status.PAID
            payment.ref_id = str(verified.get("ref_id", ""))
            payment.paid_at = timezone.now()
            payment.save(update_fields=["status", "ref_id", "paid_at"])
            return True

        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        return False

    def get_redirect_url(self, payment) -> str | None:
        if not payment.authority:
            return None
        _, _, startpay = _bases()
        return startpay + payment.authority
