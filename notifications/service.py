"""Single notification entry point (ADR-0003).

``notify(owner, event, **context)`` renders the event's templates and delivers
over SMS and/or email according to the Owner's stored preferences. This is the
skeleton; real provider backends and more events arrive in later phases.
"""
import logging

from django.core.mail import send_mail

from .events import EVENTS
from .sms import send_sms

logger = logging.getLogger("notifications")


def notify(owner, event: str, **context) -> None:
    spec = EVENTS.get(event)
    if spec is None:
        raise KeyError(f"رویداد اطلاع‌رسانی ناشناخته: {event}")

    context.setdefault("name", owner.full_name or owner.phone)
    profile = getattr(owner, "owner_profile", None)

    if profile is None or profile.notify_by_sms:
        try:
            send_sms(owner.phone, spec["sms"].format(**context))
        except Exception:
            # Notification SMS failures are logged, not raised: a non-critical
            # message should not break the calling flow (unlike OTP, which
            # surfaces failures directly through send_sms).
            logger.exception("notify SMS failed for %s event=%s", owner.phone, event)

    if owner.email and profile is not None and profile.notify_by_email:
        send_mail(
            subject=spec["email_subject"].format(**context),
            message=spec["email_body"].format(**context),
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[owner.email],
            fail_silently=True,
        )
