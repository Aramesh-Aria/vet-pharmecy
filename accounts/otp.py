"""OTP generation and verification (ADR-0004).

Codes are delivered through the shared SMS layer (ADR-0003), so an SMS gateway
outage blocks OTP login — :func:`send_otp` lets the delivery error propagate so
the caller can show a real failure rather than a silent dead end.
"""
import secrets

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from notifications.sms import send_sms

from .models import PhoneOTP

CODE_DIGITS = 6


def _new_code() -> str:
    return f"{secrets.randbelow(10**CODE_DIGITS):0{CODE_DIGITS}d}"


def send_otp(phone: str, purpose: str) -> PhoneOTP:
    """Issue a fresh OTP for *phone*/*purpose* and SMS it.

    Any previously unconsumed code for the same phone+purpose is invalidated so
    only the newest code works.
    """
    PhoneOTP.objects.filter(
        phone=phone, purpose=purpose, consumed_at__isnull=True
    ).update(consumed_at=timezone.now())

    code = _new_code()
    otp = PhoneOTP.objects.create(
        phone=phone,
        code_hash=make_password(code),
        purpose=purpose,
        expires_at=timezone.now()
        + timezone.timedelta(seconds=settings.OTP_TTL_SECONDS),
    )
    minutes = settings.OTP_TTL_SECONDS // 60
    send_sms(phone, f"کد تأیید شما: {code}\nاعتبار: {minutes} دقیقه")
    return otp


def verify_otp(phone: str, purpose: str, code: str) -> bool:
    """Return True iff *code* matches the latest usable OTP. Consumes it on
    success; counts the attempt on failure."""
    otp = (
        PhoneOTP.objects.filter(phone=phone, purpose=purpose, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if otp is None or not otp.is_usable():
        return False

    otp.attempts += 1
    if check_password(code, otp.code_hash):
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["attempts", "consumed_at"])
        return True

    otp.save(update_fields=["attempts"])
    return False
