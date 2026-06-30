import pytest
from django.test import override_settings

from accounts.models import User
from notifications.backends import locmem
from notifications.service import notify
from notifications.sms import send_sms

LOCMEM = "notifications.backends.locmem.LocMemSMSBackend"


@pytest.fixture(autouse=True)
def _clear_outbox():
    locmem.outbox.clear()
    yield
    locmem.outbox.clear()


@override_settings(SMS_BACKEND=LOCMEM)
def test_send_sms_uses_configured_backend():
    send_sms("09123456789", "سلام")
    assert locmem.outbox == [("09123456789", "سلام")]


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_notify_respects_sms_preference():
    owner = User.objects.create_user(phone="09123456789", password="Str0ngPass!9",
                                     full_name="سارا")
    notify(owner, "welcome")
    assert len(locmem.outbox) == 1
    assert "سارا" in locmem.outbox[0][1]

    owner.owner_profile.notify_by_sms = False
    owner.owner_profile.save()
    notify(owner, "welcome")
    assert len(locmem.outbox) == 1  # no new SMS sent


def test_notify_unknown_event_raises(db):
    owner = User.objects.create_user(phone="09123456789", password="Str0ngPass!9")
    with pytest.raises(KeyError):
        notify(owner, "does_not_exist")
