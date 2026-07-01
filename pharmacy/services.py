"""Store operations: cart, checkout, and order/refill lifecycle.

All money is integer Rial. Stock is reserved (decremented) when an Order is
placed and restored if it is cancelled, so the catalog can't oversell. Payment
uses the configured backend — pay-at-pickup at launch — created at placement and
settled in person when the customer collects (ADR-0005).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from payments.backends.manual import settle_in_person
from payments.services import payment_for, start_payment

from .models import Cart, CartItem, Order, OrderItem, Prescription, RefillRequest


# --- Cart ------------------------------------------------------------------
def get_cart(owner) -> Cart:
    cart, _ = Cart.objects.get_or_create(owner=owner)
    return cart


def add_to_cart(owner, product, quantity: int = 1) -> CartItem:
    if not product.orderable:
        raise ValidationError("این کالا قابل افزودن به سبد نیست.")
    if quantity < 1:
        raise ValidationError("تعداد نامعتبر است.")

    cart = get_cart(owner)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, prescription=None
    )
    new_qty = quantity if created else item.quantity + quantity
    if new_qty > product.stock:
        raise ValidationError("موجودی کافی نیست.")
    item.quantity = new_qty
    item.save()
    return item


def add_prescription_to_cart(owner, prescription, quantity: int = 1) -> CartItem:
    """Add a prescription-only medication to the cart, up to the doctor's
    authorised remaining quantity. Ordering less than the full amount now leaves
    the rest available to order later (remaining is recomputed from orders)."""
    if prescription.owner != owner:
        raise ValidationError("این نسخه متعلق به شما نیست.")
    if not prescription.is_active:
        raise ValidationError("این نسخه فعال نیست.")
    if quantity < 1:
        raise ValidationError("تعداد نامعتبر است.")

    product = prescription.product
    if not product.is_active:
        raise ValidationError("این دارو در حال حاضر در دسترس نیست.")

    cart = get_cart(owner)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, prescription=prescription
    )
    new_qty = quantity if created else item.quantity + quantity
    if new_qty > prescription.remaining_quantity:
        raise ValidationError(
            f"بیش از مقدار مجاز نسخه است (باقی‌مانده: {prescription.remaining_quantity})."
        )
    if new_qty > product.stock:
        raise ValidationError("موجودی کافی نیست.")
    item.quantity = new_qty
    item.save()
    return item


def update_cart_item(owner, product, quantity: int) -> None:
    cart = get_cart(owner)
    item = cart.items.filter(product=product).first()
    if item is None:
        return
    if quantity <= 0:
        item.delete()
        return
    if quantity > product.stock:
        raise ValidationError("موجودی کافی نیست.")
    if item.prescription and quantity > item.prescription.remaining_quantity:
        raise ValidationError("بیش از مقدار مجاز نسخه است.")
    item.quantity = quantity
    item.save()


def remove_from_cart(owner, product) -> None:
    get_cart(owner).items.filter(product=product).delete()


# --- Checkout --------------------------------------------------------------
@transaction.atomic
def place_order(owner) -> Order:
    """Turn the Owner's cart into an Order, reserve stock, and start payment."""
    cart = get_cart(owner)
    items = list(cart.items.select_related("product"))
    if not items:
        raise ValidationError("سبد خرید خالی است.")

    # Re-check stock under the transaction before committing.
    for item in items:
        if item.quantity > item.product.stock:
            raise ValidationError(f"موجودی «{item.product.name}» کافی نیست.")

    order = Order.objects.create(owner=owner)
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            unit_price=item.product.price,
            quantity=item.quantity,
            prescription=item.prescription,
        )
        # Reserve stock.
        item.product.stock -= item.quantity
        item.product.save(update_fields=["stock"])

    cart.items.all().delete()

    # Pay-at-pickup: create the (INITIATED) payment now; settle at collection.
    start_payment(order, order.total)

    _safe_notify(owner, "order_placed", order=order)
    return order


# --- Order lifecycle -------------------------------------------------------
@transaction.atomic
def set_order_status(order: Order, new_status: str) -> Order:
    """Transition an Order and run the side effects of the new status."""
    if new_status == order.status:
        return order

    if new_status == Order.Status.CANCELLED:
        _restock(order)
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    if new_status == Order.Status.COLLECTED:
        payment = payment_for(order)
        if payment is not None:
            settle_in_person(payment)  # idempotent

    event = {
        Order.Status.APPROVED: "order_approved",
        Order.Status.READY: "order_ready",
    }.get(new_status)
    if event:
        _safe_notify(order.owner, event, order=order)
    return order


def _restock(order: Order) -> None:
    for item in order.items.select_related("product"):
        if item.product is not None:
            item.product.stock += item.quantity
            item.product.save(update_fields=["stock"])


# --- Prescriptions & refills ----------------------------------------------
def request_refill(owner, prescription: Prescription, quantity: int = 1) -> RefillRequest:
    if prescription.owner != owner:
        raise ValidationError("این نسخه متعلق به شما نیست.")
    if not prescription.is_active:
        raise ValidationError("این نسخه فعال نیست.")
    return RefillRequest.objects.create(
        prescription=prescription, owner=owner, quantity=quantity
    )


@transaction.atomic
def set_refill_status(refill: RefillRequest, new_status: str) -> RefillRequest:
    """Staff transition for a refill. Approving grants the refill's quantity to
    the prescription's allowance (once), so the Owner can order that much more
    through the normal cart/Order flow. No separate price/payment is involved."""
    refill.status = new_status

    if new_status == RefillRequest.Status.APPROVED and not refill.allowance_granted:
        prescription = refill.prescription
        prescription.quantity += refill.quantity
        prescription.save(update_fields=["quantity"])
        refill.allowance_granted = True
        refill.save()
        _safe_notify(refill.owner, "refill_approved", refill=refill)
    else:
        refill.save()
    return refill


def _safe_notify(owner, event, **context) -> None:
    """Send a notification without letting a delivery error break the flow."""
    from notifications.service import notify

    try:
        notify(owner, event, **context)
    except Exception:
        pass
