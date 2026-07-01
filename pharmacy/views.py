"""Owner-facing store views: cart, checkout, orders, prescriptions, refills.

Everything is login-required and scoped to the requesting Owner.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from catalog.models import Product

from . import services
from .models import Order, Prescription, RefillRequest


# --- Cart ------------------------------------------------------------------
class CartView(LoginRequiredMixin, TemplateView):
    template_name = "pharmacy/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounts.models import OwnerProfile

        ctx["cart"] = services.get_cart(self.request.user)
        profile, _ = OwnerProfile.objects.get_or_create(user=self.request.user)
        ctx["profile_complete"] = profile.is_complete
        return ctx


@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    try:
        services.add_to_cart(request.user, product, quantity)
        messages.success(request, "به سبد افزوده شد.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    # Return to where they were (e.g. the product page) so they can keep shopping.
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("pharmacy:cart")


@login_required
@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        services.update_cart_item(request.user, product, int(request.POST.get("quantity", 0)))
    except (ValidationError, ValueError) as exc:
        messages.error(request, getattr(exc, "messages", ["مقدار نامعتبر"])[0])
    return redirect("pharmacy:cart")


@login_required
@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    services.remove_from_cart(request.user, product)
    return redirect("pharmacy:cart")


@login_required
@require_POST
def checkout(request):
    from accounts.models import OwnerProfile
    from payments.services import gateway_redirect_url

    # Orders are collected/delivered, so a complete profile (name, province,
    # city, address, postal code) is required before ordering. The cart itself
    # stays open — only placing the order is gated.
    profile, _ = OwnerProfile.objects.get_or_create(user=request.user)
    if not profile.is_complete:
        messages.error(
            request,
            "برای ثبت سفارش ابتدا پروفایل خود را کامل کنید "
            "(نام، استان، شهر، نشانی و کد پستی).",
        )
        return redirect("accounts:profile")

    try:
        order = services.place_order(request.user)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("pharmacy:cart")

    # When online payment is enabled, send the Owner to the gateway; otherwise
    # the order is settled at pickup (no redirect).
    redirect_url = gateway_redirect_url(order)
    if redirect_url:
        return redirect(redirect_url)

    messages.success(request, "سفارش شما ثبت شد. پرداخت هنگام تحویل در داروخانه.")
    return redirect(order.get_absolute_url())


# --- Orders ----------------------------------------------------------------
class OrderListView(LoginRequiredMixin, ListView):
    template_name = "pharmacy/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    template_name = "pharmacy/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(owner=self.request.user)


# --- Prescriptions & refills ----------------------------------------------
class PrescriptionListView(LoginRequiredMixin, ListView):
    template_name = "pharmacy/prescription_list.html"
    context_object_name = "prescriptions"

    def get_queryset(self):
        return Prescription.objects.filter(
            animal__owner=self.request.user
        ).select_related("animal", "product")


@login_required
@require_POST
def refill_request(request, prescription_id):
    prescription = get_object_or_404(
        Prescription, pk=prescription_id, animal__owner=request.user
    )
    try:
        quantity = int(request.POST.get("quantity", 1))
        refill = services.request_refill(request.user, prescription, quantity)
    except (ValidationError, ValueError) as exc:
        messages.error(request, getattr(exc, "messages", ["خطا"])[0])
        return redirect("pharmacy:prescriptions")
    messages.success(request, "درخواست تکرار نسخه ثبت شد.")
    return redirect(refill.get_absolute_url())


@login_required
@require_POST
def prescription_add_to_cart(request, prescription_id):
    """Add a prescribed medication to the cart, up to the doctor's authorised
    remaining quantity. It's then paid through the normal Order flow."""
    prescription = get_object_or_404(
        Prescription, pk=prescription_id, animal__owner=request.user
    )
    try:
        quantity = int(request.POST.get("quantity", 1))
        services.add_prescription_to_cart(request.user, prescription, quantity)
    except (ValidationError, ValueError) as exc:
        messages.error(request, getattr(exc, "messages", ["مقدار نامعتبر"])[0])
        return redirect("pharmacy:prescriptions")
    messages.success(request, "داروی نسخه‌ای به سبد افزوده شد.")
    return redirect("pharmacy:cart")


class RefillListView(LoginRequiredMixin, ListView):
    template_name = "pharmacy/refill_list.html"
    context_object_name = "refills"

    def get_queryset(self):
        return RefillRequest.objects.filter(owner=self.request.user).select_related(
            "prescription__product"
        )


class RefillDetailView(LoginRequiredMixin, DetailView):
    template_name = "pharmacy/refill_detail.html"
    context_object_name = "refill"

    def get_queryset(self):
        return RefillRequest.objects.filter(owner=self.request.user)
