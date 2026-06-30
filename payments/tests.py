import pytest
from django.contrib.auth import get_user_model

from payments.backends.manual import settle_in_person
from payments.models import Payment
from payments.services import start_payment, verify_payment

User = get_user_model()


@pytest.mark.django_db
def test_manual_backend_starts_without_redirect():
    # Any model instance can stand in as a payable for the stub.
    owner = User.objects.create_user(phone="09123456789", password="pw-strong-123")
    result = start_payment(owner, amount=500_000)
    payment = Payment.objects.get(pk=result.payment_id)

    assert result.redirect_url is None  # pay-at-pickup: no online redirect
    assert payment.status == Payment.Status.INITIATED
    assert payment.amount == 500_000


@pytest.mark.django_db
def test_settle_in_person_is_idempotent():
    owner = User.objects.create_user(phone="09123456789", password="pw-strong-123")
    payment = Payment.objects.get(pk=start_payment(owner, amount=1000).payment_id)

    settle_in_person(payment)
    assert payment.is_paid
    first_paid_at = payment.paid_at

    settle_in_person(payment)  # second call must not re-settle
    assert payment.paid_at == first_paid_at
    assert verify_payment(payment, {}) is True
