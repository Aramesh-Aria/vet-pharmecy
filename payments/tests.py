"""Tests for the payment backends and the online-payment flow (flagged)."""
import pytest
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import User
from catalog.models import AnimalCategory, Product, Section
from notifications.backends import locmem
from payments.backends.manual import settle_in_person
from payments.models import Payment
from payments.services import gateway_redirect_url, payment_for, start_payment, verify_payment
from pharmacy import services as shop
from pharmacy.models import Order

DUMMY = "payments.backends.dummy.DummyOnlineBackend"
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
def product(db):
    cat = AnimalCategory.objects.get(slug="companion-pets")
    return Product.objects.create(
        animal_category=cat, section=Section.MEDICATION, name="مکمل",
        slug="supp", price=300_000, stock=10,
    )


# --- Manual pay-at-pickup backend ------------------------------------------
@pytest.mark.django_db
def test_manual_backend_starts_without_redirect(owner):
    result = start_payment(owner, amount=500_000)  # any model works as payable
    payment = Payment.objects.get(pk=result.payment_id)
    assert result.redirect_url is None
    assert payment.status == Payment.Status.INITIATED
    assert payment.amount == 500_000


@pytest.mark.django_db
def test_settle_in_person_is_idempotent(owner):
    payment = Payment.objects.get(pk=start_payment(owner, amount=1000).payment_id)
    settle_in_person(payment)
    assert payment.is_paid
    first_paid_at = payment.paid_at
    settle_in_person(payment)
    assert payment.paid_at == first_paid_at
    assert verify_payment(payment, {}) is True


# --- Backend selection -----------------------------------------------------
@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_pickup_default_has_no_redirect(owner, product):
    shop.add_to_cart(owner, product, 1)
    order = shop.place_order(owner)
    assert gateway_redirect_url(order) is None  # pay-at-pickup
    assert payment_for(order).backend.endswith("ManualPickupBackend")


@override_settings(SMS_BACKEND=LOCMEM, PAYMENTS_ONLINE_ENABLED=True,
                   PAYMENTS_ONLINE_BACKEND=DUMMY)
@pytest.mark.django_db
def test_online_enabled_produces_redirect_and_records_backend(owner, product):
    shop.add_to_cart(owner, product, 1)
    order = shop.place_order(owner)
    payment = payment_for(order)
    assert payment.backend == DUMMY
    assert payment.authority  # gateway authority stored
    assert gateway_redirect_url(order).startswith("/payments/dummy-gateway/")


# --- Full flow via HTTP ----------------------------------------------------
@override_settings(SMS_BACKEND=LOCMEM, PAYMENTS_ONLINE_ENABLED=True,
                   PAYMENTS_ONLINE_BACKEND=DUMMY)
@pytest.mark.django_db
def test_checkout_redirects_to_gateway_then_callback_settles(owner, product):
    client = Client()
    client.force_login(owner)
    client.post(reverse("pharmacy:cart_add", args=[product.pk]), {"quantity": 2})

    resp = client.post(reverse("pharmacy:checkout"))
    assert resp.status_code == 302
    assert "/payments/dummy-gateway/" in resp.url  # off to the gateway

    order = Order.objects.get(owner=owner)
    payment = payment_for(order)

    # Simulate the gateway returning the Owner to our callback.
    cb = client.get(reverse("payments:callback"),
                    {"Authority": payment.authority, "Status": "OK"})
    assert cb.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert payment.ref_id


@override_settings(SMS_BACKEND=LOCMEM, PAYMENTS_ONLINE_ENABLED=True,
                   PAYMENTS_ONLINE_BACKEND=DUMMY)
@pytest.mark.django_db
def test_failed_callback_marks_failed(owner, product):
    shop.add_to_cart(owner, product, 1)
    order = shop.place_order(owner)
    payment = payment_for(order)

    Client().get(reverse("payments:callback"),
                 {"Authority": payment.authority, "Status": "NOK"})
    payment.refresh_from_db()
    assert payment.status == Payment.Status.FAILED


@override_settings(SMS_BACKEND=LOCMEM, PAYMENTS_ONLINE_ENABLED=True,
                   PAYMENTS_ONLINE_BACKEND=DUMMY)
@pytest.mark.django_db
def test_callback_is_idempotent(owner, product):
    shop.add_to_cart(owner, product, 1)
    order = shop.place_order(owner)
    payment = payment_for(order)
    args = {"Authority": payment.authority, "Status": "OK"}

    Client().get(reverse("payments:callback"), args)
    Client().get(reverse("payments:callback"), args)  # second time: no error
    payment.refresh_from_db()
    assert payment.status == Payment.Status.PAID
