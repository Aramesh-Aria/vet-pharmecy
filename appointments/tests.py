"""Tests for the appointment request → staff-confirm flow."""
import datetime

import pytest
from django.core.exceptions import ValidationError
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from animals.models import Animal
from appointments import services
from appointments.models import Appointment
from catalog.models import AnimalCategory, Service
from notifications.backends import locmem

LOCMEM = "notifications.backends.locmem.LocMemSMSBackend"


@pytest.fixture(autouse=True)
def _clear_outbox():
    locmem.outbox.clear()
    yield
    locmem.outbox.clear()


@pytest.fixture
def owner(db):
    return User.objects.create_user(phone="09120000001", password="Str0ngPass!9")


@pytest.fixture
def animal(owner):
    cat = AnimalCategory.objects.get(slug="companion-pets")
    return Animal.objects.create(owner=owner, animal_category=cat, name="رکس", species="سگ")


@pytest.fixture
def service(db):
    cat = AnimalCategory.objects.get(slug="companion-pets")
    return Service.objects.create(
        animal_category=cat, name="معاینه", slug="checkup", duration_minutes=30
    )


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_request_appointment_creates_requested(owner, animal, service):
    appt = services.request_appointment(
        owner, animal=animal, service=service,
        preferred_date=timezone.localdate() + datetime.timedelta(days=2),
    )
    assert appt.status == Appointment.Status.REQUESTED
    assert any("نوبت" in msg for _, msg in locmem.outbox)


@pytest.mark.django_db
def test_request_rejects_foreign_animal(service, db):
    owner = User.objects.create_user(phone="09120000005", password="Str0ngPass!9")
    other = User.objects.create_user(phone="09120000006", password="Str0ngPass!9")
    cat = AnimalCategory.objects.get(slug="companion-pets")
    foreign = Animal.objects.create(owner=other, animal_category=cat, name="غریبه", species="گربه")
    with pytest.raises(ValidationError):
        services.request_appointment(
            owner, animal=foreign, service=service, preferred_date=timezone.localdate()
        )


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_confirm_requires_datetime_then_notifies(owner, animal, service):
    appt = services.request_appointment(
        owner, animal=animal, service=service, preferred_date=timezone.localdate()
    )
    with pytest.raises(ValidationError):
        services.set_appointment_status(appt, Appointment.Status.CONFIRMED)

    when = timezone.now() + datetime.timedelta(days=1)
    locmem.outbox.clear()
    services.set_appointment_status(appt, Appointment.Status.CONFIRMED, confirmed_datetime=when)
    appt.refresh_from_db()
    assert appt.status == Appointment.Status.CONFIRMED
    assert appt.confirmed_datetime == when
    assert any("تأیید" in msg for _, msg in locmem.outbox)


@pytest.mark.django_db
def test_owner_can_cancel_but_not_after_completion(owner, animal, service):
    appt = services.request_appointment(
        owner, animal=animal, service=service, preferred_date=timezone.localdate()
    )
    services.cancel_by_owner(appt, owner)
    assert appt.status == Appointment.Status.CANCELLED

    appt2 = services.request_appointment(
        owner, animal=animal, service=service, preferred_date=timezone.localdate()
    )
    services.set_appointment_status(appt2, Appointment.Status.COMPLETED)
    with pytest.raises(ValidationError):
        services.cancel_by_owner(appt2, owner)


@pytest.mark.django_db
def test_appointment_detail_scoped_to_owner(owner, animal, service):
    appt = services.request_appointment(
        owner, animal=animal, service=service, preferred_date=timezone.localdate()
    )
    stranger = User.objects.create_user(phone="09120000009", password="Str0ngPass!9")
    client = Client()
    client.force_login(stranger)
    assert client.get(reverse("appointments:detail", args=[appt.pk])).status_code == 404
