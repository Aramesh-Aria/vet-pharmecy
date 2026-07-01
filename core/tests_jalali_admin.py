"""Tests for Jalali date widgets and their use in the admin."""
import datetime

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from animals.models import Animal
from catalog.models import AnimalCategory
from core.widgets import JalaliDateInput, JalaliSplitDateTimeField


def test_jalali_date_input_shows_jalali_submits_gregorian():
    html = JalaliDateInput().render("d", datetime.date(2024, 6, 30))
    assert "۱۴۰۳/۰۴/۱۰" in html          # Jalali shown to the user
    assert 'value="2024-06-30"' in html   # Gregorian submitted (hidden)
    assert "data-jdate" in html
    # round-trips back to the Gregorian string on submit
    assert JalaliDateInput().value_from_datadict({"d": "2024-06-30"}, {}, "d") == "2024-06-30"


def test_split_datetime_field_combines_date_and_time():
    field = JalaliSplitDateTimeField(required=False)
    values = field.widget.value_from_datadict(
        {"x_0": "2024-07-01", "x_1": "14:30"}, {}, "x"
    )
    assert field.clean(values) == datetime.datetime(2024, 7, 1, 14, 30)


@pytest.mark.django_db
def test_admin_vaccination_form_is_jalali_and_saves_gregorian():
    admin = User.objects.create_superuser(phone="09120000000", password="Str0ngPass!9")
    cat = AnimalCategory.objects.get(slug="companion-pets")
    animal = Animal.objects.create(owner=admin, animal_category=cat, name="رکس", species="سگ")

    client = Client()
    client.force_login(admin)

    add_url = reverse("admin:records_vaccination_add")
    page = client.get(add_url)
    assert page.status_code == 200
    body = page.content.decode()
    assert "data-jdate" in body              # Jalali picker rendered
    assert "admin_jalali.css" in body        # styles loaded

    resp = client.post(add_url, {
        "animal": animal.pk,
        "vaccine_name": "هاری",
        "date_given": "2024-06-30",          # Gregorian from the hidden field
        "next_due": "2025-06-30",
        "notes": "",
    })
    assert resp.status_code == 302           # saved + redirected to changelist
    from records.models import Vaccination
    vac = Vaccination.objects.get(vaccine_name="هاری")
    assert vac.date_given == datetime.date(2024, 6, 30)
    assert vac.next_due == datetime.date(2025, 6, 30)
