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
    client.get(reverse("accounts:register"))  # seed the captcha challenge
    client.post(
        reverse("accounts:register"),
        {
            "phone": "09121112222",
            "full_name": "سارا",
            "password1": "Str0ngPass!9",
            "password2": "Str0ngPass!9",
            "captcha": str(client.session["captcha_answer"]),
        },
    )
    code = re.search(r"(\d{6})", locmem.outbox[-1][1]).group(1)
    resp = client.post(reverse("accounts:register_verify"), {"code": code})
    assert resp.status_code == 302
    assert resp.url == reverse("accounts:profile")


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_registration_rejected_with_wrong_captcha():
    client = Client()
    client.get(reverse("accounts:register"))  # a challenge now exists
    resp = client.post(
        reverse("accounts:register"),
        {
            "phone": "09121113333",
            "full_name": "نادر",
            "password1": "Str0ngPass!9",
            "password2": "Str0ngPass!9",
            "captcha": "0",  # deliberately wrong
        },
    )
    assert resp.status_code == 200  # re-rendered, not created
    assert not User.objects.filter(phone="09121113333").exists()
    assert "کد امنیتی" in resp.content.decode()


@pytest.mark.django_db
def test_login_requires_correct_captcha(owner):
    owner.set_password("Str0ngPass!9")
    owner.phone_verified = True
    owner.save()
    client = Client()
    client.get(reverse("accounts:login"))

    # Wrong captcha → not logged in.
    client.post(reverse("accounts:login"), {
        "username": owner.phone, "password": "Str0ngPass!9", "captcha": "0",
    })
    assert "_auth_user_id" not in client.session

    # Correct captcha → logged in.
    client.get(reverse("accounts:login"))
    ok = client.post(reverse("accounts:login"), {
        "username": owner.phone, "password": "Str0ngPass!9",
        "captcha": str(client.session["captcha_answer"]),
    })
    assert ok.status_code == 302
    assert "_auth_user_id" in client.session
