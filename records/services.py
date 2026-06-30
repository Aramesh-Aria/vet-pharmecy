"""Vaccination reminders (PLAN §3).

Cron runs ``send_vaccination_reminders`` (a management command) which calls
:func:`send_due_reminders`. ``reminded_at`` guards against repeat reminders for
the same vaccination.
"""
from django.conf import settings
from django.utils import timezone

from notifications.service import notify

from .models import Vaccination


def due_vaccinations(window_days: int | None = None):
    """Vaccinations whose next_due falls within the reminder window and that
    haven't been reminded yet."""
    if window_days is None:
        window_days = getattr(settings, "VACCINATION_REMINDER_DAYS", 7)
    today = timezone.localdate()
    horizon = today + timezone.timedelta(days=window_days)
    return Vaccination.objects.filter(
        reminded_at__isnull=True,
        next_due__isnull=False,
        next_due__lte=horizon,
    ).select_related("animal", "animal__owner")


def send_due_reminders(window_days: int | None = None) -> int:
    """Notify owners of upcoming vaccinations. Returns the count sent."""
    sent = 0
    for vac in due_vaccinations(window_days):
        owner = vac.animal.owner
        try:
            notify(owner, "vaccination_due", vaccination=vac)
        except Exception:
            continue  # leave reminded_at unset so the next run retries
        vac.reminded_at = timezone.now()
        vac.save(update_fields=["reminded_at"])
        sent += 1
    return sent
