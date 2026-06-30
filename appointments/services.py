"""Appointment lifecycle. Owners request; Staff confirm/complete/decline.

There is no live calendar in v1 (PLAN §2): the Owner submits a preferred date
and Staff set a confirmed time. Status changes notify the Owner.
"""
from django.core.exceptions import ValidationError

from .models import Appointment


def request_appointment(owner, *, animal, service, preferred_date,
                        preferred_time_note="", owner_note="") -> Appointment:
    if animal is None or animal.owner_id != owner.pk:
        raise ValidationError("حیوان انتخاب‌شده متعلق به شما نیست.")
    appointment = Appointment(
        owner=owner,
        animal=animal,
        service=service,
        preferred_date=preferred_date,
        preferred_time_note=preferred_time_note,
        owner_note=owner_note,
    )
    appointment.full_clean()
    appointment.save()
    _safe_notify(owner, "appointment_requested", appointment=appointment)
    return appointment


def set_appointment_status(appointment, new_status, *, confirmed_datetime=None,
                           vet=None) -> Appointment:
    if confirmed_datetime is not None:
        appointment.confirmed_datetime = confirmed_datetime
    if vet is not None:
        appointment.vet = vet

    if new_status == Appointment.Status.CONFIRMED and appointment.confirmed_datetime is None:
        raise ValidationError("برای تأیید، زمان تأییدشده را وارد کنید.")

    appointment.status = new_status
    appointment.save()

    event = {
        Appointment.Status.CONFIRMED: "appointment_confirmed",
        Appointment.Status.CANCELLED: "appointment_cancelled",
        Appointment.Status.COMPLETED: "appointment_completed",
    }.get(new_status)
    if event:
        _safe_notify(appointment.owner, event, appointment=appointment)
    return appointment


def cancel_by_owner(appointment, owner) -> Appointment:
    if appointment.owner_id != owner.pk:
        raise ValidationError("این نوبت متعلق به شما نیست.")
    if not appointment.is_cancellable:
        raise ValidationError("این نوبت قابل لغو نیست.")
    return set_appointment_status(appointment, Appointment.Status.CANCELLED)


def _safe_notify(owner, event, **context) -> None:
    from notifications.service import notify

    try:
        notify(owner, event, **context)
    except Exception:
        pass
