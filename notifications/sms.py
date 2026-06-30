"""SMS delivery entry point. OTP and notifications share this layer (ADR-0003)."""
from django.conf import settings
from django.utils.module_loading import import_string

from .backends.base import BaseSMSBackend


def get_sms_backend() -> BaseSMSBackend:
    return import_string(settings.SMS_BACKEND)()


def send_sms(phone: str, message: str) -> None:
    """Send an SMS via the configured backend. Raises SMSDeliveryError on
    failure — callers must handle it rather than assume success."""
    get_sms_backend().send(phone, message)
