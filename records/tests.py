"""Tests for visit records, vaccinations, and the reminder job."""
import datetime

import pytest
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from animals.models import Animal
from catalog.models import AnimalCategory
from notifications.backends import locmem
from records.models import Vaccination, VisitRecord
from records.services import send_due_reminders

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


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_reminder_sent_once_for_due_vaccination(animal):
    Vaccination.objects.create(
        animal=animal, vaccine_name="هاری",
        date_given=timezone.localdate() - datetime.timedelta(days=350),
        next_due=timezone.localdate() + datetime.timedelta(days=3),
    )
    assert send_due_reminders() == 1
    assert len(locmem.outbox) == 1
    # Second run does not re-notify (reminded_at now set).
    assert send_due_reminders() == 0
    assert len(locmem.outbox) == 1


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_far_future_vaccination_not_reminded(animal):
    Vaccination.objects.create(
        animal=animal, vaccine_name="هاری",
        date_given=timezone.localdate(),
        next_due=timezone.localdate() + datetime.timedelta(days=60),
    )
    assert send_due_reminders() == 0
    assert locmem.outbox == []


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_management_command_runs(animal):
    from django.core.management import call_command

    Vaccination.objects.create(
        animal=animal, vaccine_name="هاری", date_given=timezone.localdate(),
        next_due=timezone.localdate(),
    )
    call_command("send_vaccination_reminders")
    assert len(locmem.outbox) == 1


@pytest.mark.django_db
def test_visit_history_shown_on_animal_detail(owner, animal):
    VisitRecord.objects.create(
        animal=animal, date=timezone.localdate(), notes="معاینهٔ سالانه انجام شد"
    )
    client = Client()
    client.force_login(owner)
    body = client.get(reverse("animals:detail", args=[animal.pk])).content.decode()
    assert "معاینهٔ سالانه انجام شد" in body
