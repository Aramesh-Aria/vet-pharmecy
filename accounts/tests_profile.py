"""Tests for postal code + post-registration profile completion."""
import re

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import User
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


def _complete_profile_post():
    return {
        "full_name": "علی رضایی",
        "email": "",
        "province": "مازندران",
        "city": "آمل",
        "address": "آمل، خیابان امام",
        "postal_code": "۱۲۳۴۵۶۷۸۹۰",  # Persian digits
    }


@pytest.mark.django_db
def test_profile_saves_postal_code_normalising_persian_digits(owner):
    client = Client()
    client.force_login(owner)
    resp = client.post(reverse("accounts:profile"), _complete_profile_post())
    assert resp.status_code == 302
    owner.refresh_from_db()
    assert owner.owner_profile.postal_code == "1234567890"
    assert owner.owner_profile.province == "مازندران"
    assert owner.owner_profile.city == "آمل"
    assert owner.owner_profile.is_complete


@pytest.mark.django_db
def test_profile_rejects_bad_postal_code(owner):
    client = Client()
    client.force_login(owner)
    resp = client.post(
        reverse("accounts:profile"),
        {"full_name": "علی", "email": "", "address": "آمل", "postal_code": "123"},
    )
    assert resp.status_code == 200  # re-rendered with error
    owner.refresh_from_db()
    assert owner.owner_profile.postal_code == ""


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_registration_redirects_to_profile_completion():
    client = Client()
    client.post(
        reverse("accounts:register"),
        {
            "phone": "09121112222",
            "full_name": "سارا",
            "password1": "Str0ngPass!9",
            "password2": "Str0ngPass!9",
        },
    )
    code = re.search(r"(\d{6})", locmem.outbox[-1][1]).group(1)
    resp = client.post(reverse("accounts:register_verify"), {"code": code})
    assert resp.status_code == 302
    assert resp.url == reverse("accounts:profile")
