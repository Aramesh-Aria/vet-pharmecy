"""Public entry points for the payments app (ADR-0005).

Callers use :func:`start_payment` / :func:`verify_payment` and never import a
backend directly, so the launch pay-at-pickup backend can be swapped for a real
gateway by changing ``settings.PAYMENTS_BACKEND`` alone.
"""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.module_loading import import_string

from .backends.base import BasePaymentBackend, StartResult
from .models import Payment


def get_backend() -> BasePaymentBackend:
    return import_string(settings.PAYMENTS_BACKEND)()


def start_payment(payable, amount: int) -> StartResult:
    """Create a Payment for *payable* and start it on the active backend."""
    backend = get_backend()
    payment = Payment.objects.create(
        content_type=ContentType.objects.get_for_model(payable),
        object_id=payable.pk,
        amount=amount,
        backend=settings.PAYMENTS_BACKEND,
    )
    return backend.start(payment)


def verify_payment(payment: Payment, data: dict) -> bool:
    """Verify a payment via its originating backend (idempotent)."""
    backend = import_string(payment.backend)()
    return backend.verify(payment, data)


def payment_for(payable) -> Payment | None:
    """Return the most recent Payment attached to *payable*, if any."""
    return (
        Payment.objects.filter(
            content_type=ContentType.objects.get_for_model(payable),
            object_id=payable.pk,
        )
        .order_by("-created_at")
        .first()
    )
