"""Tests for the OTP registration and password-reset flows (ADR-0004)."""
import re

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import PhoneOTP, User
from accounts.otp import send_otp, verify_otp
from notifications.backends import locmem

LOCMEM = "notifications.backends.locmem.LocMemSMSBackend"


@pytest.fixture(autouse=True)
def _clear_outbox():
    locmem.outbox.clear()
    yield
    locmem.outbox.clear()


def _last_code() -> str:
    return re.search(r"(\d{6})", locmem.outbox[-1][1]).group(1)


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_send_and_verify_otp_roundtrip():
    send_otp("09123456789", PhoneOTP.Purpose.REGISTER)
    code = _last_code()
    assert verify_otp("09123456789", "register", code) is True
    # second use of the same (now consumed) code fails
    assert verify_otp("09123456789", "register", code) is False


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_verify_otp_wrong_code_counts_attempt():
    send_otp("09123456789", PhoneOTP.Purpose.REGISTER)
    assert verify_otp("09123456789", "register", "000000") is False
    otp = PhoneOTP.objects.get(phone="09123456789")
    assert otp.attempts == 1
    assert otp.consumed_at is None


@override_settings(SMS_BACKEND=LOCMEM, OTP_MAX_ATTEMPTS=2)
@pytest.mark.django_db
def test_otp_locks_after_max_attempts():
    send_otp("09123456789", "register")
    code = _last_code()
    assert verify_otp("09123456789", "register", "111111") is False
    assert verify_otp("09123456789", "register", "222222") is False
    # max attempts reached -> even the correct code now fails
    assert verify_otp("09123456789", "register", code) is False


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_registration_flow_creates_verified_owner():
    client = Client()
    client.get(reverse("accounts:register"))  # seed the captcha challenge
    resp = client.post(
        reverse("accounts:register"),
        {
            "phone": "09123456789",
            "full_name": "علی رضایی",
            "password1": "Str0ngPass!9",
            "password2": "Str0ngPass!9",
            "captcha": str(client.session["captcha_answer"]),
        },
    )
    assert resp.status_code == 302
    assert not User.objects.filter(phone="09123456789").exists()  # not yet created

    code = _last_code()
    resp = client.post(reverse("accounts:register_verify"), {"code": code})
    assert resp.status_code == 302

    user = User.objects.get(phone="09123456789")
    assert user.phone_verified
    assert user.is_owner
    assert user.check_password("Str0ngPass!9")
    assert "_auth_user_id" in client.session  # logged in


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_password_reset_flow_changes_password():
    user = User.objects.create_user(phone="09123456789", password="OldPass!123")
    client = Client()

    client.post(reverse("accounts:reset"), {"phone": "09123456789"})
    code = _last_code()
    resp = client.post(
        reverse("accounts:reset_confirm"),
        {"code": code, "password1": "NewPass!456", "password2": "NewPass!456"},
    )
    assert resp.status_code == 302

    user.refresh_from_db()
    assert user.check_password("NewPass!456")
