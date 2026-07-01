"""Tests for the store: cart, checkout/order lifecycle, prescriptions, refills."""
import pytest
from django.core.exceptions import ValidationError
from django.test import Client, override_settings
from django.urls import reverse

from accounts.models import User
from animals.models import Animal
from catalog.models import AnimalCategory, Product, Section
from notifications.backends import locmem
from payments.models import Payment
from payments.services import payment_for
from pharmacy import services
from pharmacy.models import Order, Prescription, RefillRequest

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
def category(db):
    return AnimalCategory.objects.get(slug="companion-pets")


@pytest.fixture
def product(category):
    return Product.objects.create(
        animal_category=category, section=Section.MEDICATION, name="مکمل",
        slug="supplement", price=500_000, stock=10,
    )


@pytest.fixture
def rx_product(category):
    return Product.objects.create(
        animal_category=category, section=Section.MEDICATION, name="آنتی‌بیوتیک",
        slug="antibiotic", price=800_000, stock=5, is_prescription_only=True,
    )


# --- Cart ------------------------------------------------------------------
@pytest.mark.django_db
def test_add_to_cart_and_total(owner, product):
    services.add_to_cart(owner, product, 3)
    cart = services.get_cart(owner)
    assert cart.item_count == 3
    assert cart.total == 1_500_000


@pytest.mark.django_db
def test_cannot_add_prescription_only_to_cart(owner, rx_product):
    with pytest.raises(ValidationError):
        services.add_to_cart(owner, rx_product, 1)


@pytest.mark.django_db
def test_cannot_add_more_than_stock(owner, product):
    with pytest.raises(ValidationError):
        services.add_to_cart(owner, product, 99)


# --- Checkout / order lifecycle -------------------------------------------
@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_checkout_creates_order_reserves_stock_and_payment(owner, product):
    services.add_to_cart(owner, product, 2)
    order = services.place_order(owner)

    assert order.status == Order.Status.PLACED
    assert order.total == 1_000_000
    product.refresh_from_db()
    assert product.stock == 8  # reserved
    assert services.get_cart(owner).items.count() == 0  # cart cleared

    payment = payment_for(order)
    assert payment is not None
    assert payment.status == Payment.Status.INITIATED  # pay-at-pickup
    assert any("سفارش" in msg for _, msg in locmem.outbox)  # notified


@pytest.mark.django_db
def test_checkout_empty_cart_raises(owner):
    with pytest.raises(ValidationError):
        services.place_order(owner)


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_collected_settles_payment(owner, product):
    services.add_to_cart(owner, product, 1)
    order = services.place_order(owner)
    services.set_order_status(order, Order.Status.COLLECTED)
    assert payment_for(order).status == Payment.Status.PAID


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_cancel_restocks(owner, product):
    services.add_to_cart(owner, product, 4)
    order = services.place_order(owner)
    product.refresh_from_db()
    assert product.stock == 6
    services.set_order_status(order, Order.Status.CANCELLED)
    product.refresh_from_db()
    assert product.stock == 10  # restored


def _complete_profile(owner):
    owner.full_name = "علی رضایی"
    owner.save()
    p = owner.owner_profile
    p.province, p.city, p.address, p.postal_code = "مازندران", "آمل", "آمل", "1234567890"
    p.save()


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_cart_add_and_checkout_via_http(owner, product):
    _complete_profile(owner)
    client = Client()
    client.force_login(owner)

    resp = client.post(reverse("pharmacy:cart_add", args=[product.pk]), {"quantity": 2})
    assert resp.status_code == 302
    assert services.get_cart(owner).item_count == 2

    resp = client.post(reverse("pharmacy:checkout"))
    assert resp.status_code == 302
    order = Order.objects.get(owner=owner)
    assert order.total == 1_000_000
    assert resp.url == order.get_absolute_url()


@pytest.mark.django_db
def test_checkout_blocked_until_profile_complete(owner, product):
    client = Client()
    client.force_login(owner)
    services.add_to_cart(owner, product, 1)

    # Incomplete profile → checkout is refused and nothing is ordered.
    resp = client.post(reverse("pharmacy:checkout"))
    assert resp.status_code == 302
    assert resp.url == reverse("accounts:profile")
    assert Order.objects.filter(owner=owner).count() == 0

    # Cart itself stays usable while the profile is incomplete.
    assert services.get_cart(owner).item_count == 1

    # Once complete, the same checkout succeeds.
    _complete_profile(owner)
    resp = client.post(reverse("pharmacy:checkout"))
    assert resp.status_code == 302
    assert Order.objects.filter(owner=owner).count() == 1


@pytest.mark.django_db
def test_order_scoped_to_owner(owner, product):
    other = User.objects.create_user(phone="09120000002", password="Str0ngPass!9")
    services.add_to_cart(owner, product, 1)
    order = services.place_order(owner)

    client = Client()
    client.force_login(other)
    assert client.get(reverse("pharmacy:order_detail", args=[order.pk])).status_code == 404


# --- Prescriptions & refills ----------------------------------------------
@pytest.fixture
def prescription(owner, category, rx_product):
    animal = Animal.objects.create(
        owner=owner, animal_category=category, name="رکس", species="سگ"
    )
    vet = User.objects.create_user(phone="09120000003", password="Str0ngPass!9")
    return Prescription.objects.create(
        animal=animal, product=rx_product, issued_by=vet, refills_allowed=2
    )


@pytest.mark.django_db
def test_prescription_requires_prescription_only_product(owner, category, product):
    animal = Animal.objects.create(
        owner=owner, animal_category=category, name="رکس", species="سگ"
    )
    rx = Prescription(animal=animal, product=product, issued_by=owner)
    with pytest.raises(ValidationError):
        rx.full_clean()


@pytest.fixture
def prescription_for_pet(owner, category, rx_product):
    rx_product.stock = 50  # enough stock to exercise the full allowance
    rx_product.save()
    animal = Animal.objects.create(
        owner=owner, animal_category=category, name="پشمک", species="گربه"
    )
    vet = User.objects.create_user(phone="09120000044", password="Str0ngPass!9")
    return Prescription.objects.create(
        animal=animal, product=rx_product, issued_by=vet, quantity=10
    )


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_order_prescription_up_to_allowance_and_remainder_later(owner, prescription_for_pet):
    rx = prescription_for_pet
    assert rx.remaining_quantity == 10

    # Order 4 of 10 now.
    services.add_prescription_to_cart(owner, rx, 4)
    order = services.place_order(owner)
    assert order.items.get().prescription_id == rx.pk
    assert rx.remaining_quantity == 6  # 4 ordered

    # Come back and order 6 more — down to zero.
    services.add_prescription_to_cart(owner, rx, 6)
    services.place_order(owner)
    assert rx.remaining_quantity == 0
    assert not rx.is_orderable


@pytest.mark.django_db
def test_cannot_order_more_than_prescribed(owner, prescription_for_pet):
    with pytest.raises(ValidationError):
        services.add_prescription_to_cart(owner, prescription_for_pet, 11)


@pytest.mark.django_db
def test_cancelled_order_restores_prescription_allowance(owner, prescription_for_pet):
    rx = prescription_for_pet
    services.add_prescription_to_cart(owner, rx, 5)
    order = services.place_order(owner)
    assert rx.remaining_quantity == 5
    services.set_order_status(order, Order.Status.CANCELLED)
    assert rx.remaining_quantity == 10  # freed again


@pytest.mark.django_db
def test_prescription_only_still_blocked_from_plain_cart(owner, rx_product):
    # The OTC path must still refuse prescription-only meds (must use the Rx flow).
    with pytest.raises(ValidationError):
        services.add_to_cart(owner, rx_product, 1)


@pytest.mark.django_db
def test_prescription_add_rejects_foreign_owner(prescription_for_pet):
    stranger = User.objects.create_user(phone="09120000099", password="Str0ngPass!9")
    with pytest.raises(ValidationError):
        services.add_prescription_to_cart(stranger, prescription_for_pet, 1)


@pytest.mark.django_db
def test_prescription_rejects_product_from_other_category(owner, category):
    # A bird medication must not be prescribable for a cat (different category).
    birds = AnimalCategory.objects.get(slug="ornamental-birds")
    bird_med = Product.objects.create(
        animal_category=birds, section=Section.MEDICATION, name="داروی پرنده",
        slug="bird-med", price=500_000, stock=5, is_prescription_only=True,
    )
    cat = Animal.objects.create(
        owner=owner, animal_category=category, name="پشمک", species="گربه"
    )
    rx = Prescription(animal=cat, product=bird_med, issued_by=owner)
    with pytest.raises(ValidationError) as exc:
        rx.full_clean()
    assert "product" in exc.value.error_dict


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_refill_approve_grants_allowance_no_price(owner, prescription):
    before = prescription.quantity
    refill = services.request_refill(owner, prescription, 3)
    assert refill.status == RefillRequest.Status.REQUESTED

    # Approving grants the quantity to the prescription; no price/payment.
    services.set_refill_status(refill, RefillRequest.Status.APPROVED)
    refill.refresh_from_db()
    prescription.refresh_from_db()
    assert refill.status == RefillRequest.Status.APPROVED
    assert refill.allowance_granted
    assert prescription.quantity == before + 3
    assert payment_for(refill) is None


@pytest.mark.django_db
def test_refill_approve_is_idempotent(owner, prescription):
    before = prescription.quantity
    refill = services.request_refill(owner, prescription, 2)
    services.set_refill_status(refill, RefillRequest.Status.APPROVED)
    services.set_refill_status(refill, RefillRequest.Status.APPROVED)  # re-saved
    prescription.refresh_from_db()
    assert prescription.quantity == before + 2  # granted only once


@pytest.mark.django_db
def test_request_refill_rejects_foreign_prescription(prescription):
    stranger = User.objects.create_user(phone="09120000009", password="Str0ngPass!9")
    with pytest.raises(ValidationError):
        services.request_refill(stranger, prescription, 1)


@override_settings(SMS_BACKEND=LOCMEM)
@pytest.mark.django_db
def test_admin_can_approve_refill_without_price(owner, prescription):
    # Reproduces the reported bug: approving a refill in the admin no longer
    # demands a price; it grants the quantity to the prescription instead.
    admin = User.objects.create_superuser(phone="09120000000", password="Str0ngPass!9")
    refill = services.request_refill(owner, prescription, 2)
    before = prescription.quantity

    client = Client()
    client.force_login(admin)
    url = reverse("admin:pharmacy_refillrequest_change", args=[refill.pk])
    resp = client.post(url, {
        "prescription": prescription.pk,
        "owner": owner.pk,
        "quantity": refill.quantity,
        "status": "approved",
        "staff_note": "",
    })
    assert resp.status_code == 302  # saved without a ValidationError
    prescription.refresh_from_db()
    assert prescription.quantity == before + 2
