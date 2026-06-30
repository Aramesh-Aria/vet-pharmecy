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


def active_backend_path() -> str:
    """Dotted path of the backend in force: online gateway when enabled."""
    if getattr(settings, "PAYMENTS_ONLINE_ENABLED", False):
        return settings.PAYMENTS_ONLINE_BACKEND
    return settings.PAYMENTS_BACKEND


def get_backend() -> BasePaymentBackend:
    """The active backend: online gateway when enabled, else pay-at-pickup."""
    return import_string(active_backend_path())()


def start_payment(payable, amount: int) -> StartResult:
    """Create a Payment for *payable* and start it on the active backend."""
    path = active_backend_path()
    payment = Payment.objects.create(
        content_type=ContentType.objects.get_for_model(payable),
        object_id=payable.pk,
        amount=amount,
        backend=path,  # record the backend actually used, for verify dispatch
    )
    return import_string(path)().start(payment)


def gateway_redirect_url(payable) -> str | None:
    """Where to send the Owner to pay for *payable*, or None for pay-at-pickup."""
    payment = payment_for(payable)
    if payment is None:
        return None
    return import_string(payment.backend)().get_redirect_url(payment)


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
