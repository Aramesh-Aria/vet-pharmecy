import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from accounts.validators import normalize_phone

User = get_user_model()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("09123456789", "09123456789"),
        ("+989123456789", "09123456789"),
        ("00989123456789", "09123456789"),
        ("989123456789", "09123456789"),
        ("9123456789", "09123456789"),
        ("0912 345 6789", "09123456789"),
        ("۰۹۱۲۳۴۵۶۷۸۹", "09123456789"),  # Persian digits
    ],
)
def test_normalize_phone_accepts_common_forms(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("bad", ["", "12345", "0812345678", "0912345678a"])
def test_normalize_phone_rejects_invalid(bad):
    with pytest.raises(ValidationError):
        normalize_phone(bad)


@pytest.mark.django_db
def test_create_owner_gets_profile_and_role():
    user = User.objects.create_user(phone="09123456789", password="pw-strong-123")
    assert user.is_owner
    assert user.role == User.Role.OWNER
    assert not user.is_staff
    assert hasattr(user, "owner_profile")  # auto-created by signal


@pytest.mark.django_db
def test_create_superuser_is_staff_role():
    admin = User.objects.create_superuser(phone="09120000000", password="pw-strong-123")
    assert admin.is_staff and admin.is_superuser
    assert admin.role == User.Role.STAFF
    assert admin.phone_verified


@pytest.mark.django_db
def test_phone_is_normalized_on_create():
    user = User.objects.create_user(phone="+989120000001", password="pw-strong-123")
    assert user.phone == "09120000001"
