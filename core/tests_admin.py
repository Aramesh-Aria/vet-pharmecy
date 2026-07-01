"""Smoke tests for the customised admin dashboard."""
import datetime

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from animals.models import Animal
from appointments.models import Appointment
from catalog.models import AnimalCategory, Service
from records.models import Vaccination


@pytest.mark.django_db
def test_admin_app_list_uses_workflow_sections():
    from django.test import RequestFactory

    from core.admin_site import VetAdminSite

    admin = User.objects.create_superuser(phone="09120000000", password="Str0ngPass!9")
    request = RequestFactory().get("/admin/")
    request.user = admin

    site = VetAdminSite()
    # Register the models the way the real site does isn't needed; reuse default.
    from django.contrib import admin as djadmin

    site._registry = djadmin.site._registry
    app_list = site.get_app_list(request)
    section_names = [a["name"] for a in app_list]
    assert "درمانگاه" in section_names
    assert "داروخانه و سفارش‌ها" in section_names

    clinic = next(a for a in app_list if a["name"] == "درمانگاه")
    model_names = [m["object_name"] for m in clinic["models"]]
    assert {"Appointment", "Vaccination", "VisitRecord", "Prescription"} <= set(model_names)


@pytest.mark.django_db
def test_admin_index_shows_dashboard_queues():
    admin = User.objects.create_superuser(phone="09120000000", password="Str0ngPass!9")
    cat = AnimalCategory.objects.get(slug="companion-pets")
    animal = Animal.objects.create(owner=admin, animal_category=cat, name="رکس", species="سگ")
    service = Service.objects.create(animal_category=cat, name="معاینه", slug="chk")

    # One pending appointment and one due vaccination should be counted.
    Appointment.objects.create(
        owner=admin, animal=animal, service=service,
        preferred_date=timezone.localdate(),
    )
    Vaccination.objects.create(
        animal=animal, vaccine_name="هاری", date_given=timezone.localdate(),
        next_due=timezone.localdate() + datetime.timedelta(days=2),
    )

    client = Client()
    client.force_login(admin)
    resp = client.get(reverse("admin:index"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "کارهای در انتظار" in body
    assert "درخواست‌های نوبت در انتظار" in body
    assert "واکسیناسیون‌های نزدیک به موعد" in body
