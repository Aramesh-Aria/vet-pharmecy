"""Gateway callback handling (ADR-0005).

The gateway redirects the Owner back here after payment. We verify (idempotent)
and show a result page. Verification reconciles Payment ↔ gateway state; the
linked Order/RefillRequest is settled by the verify step marking the Payment paid.
"""
from django.shortcuts import get_object_or_404, render

from .models import Payment
from .services import verify_payment


def payment_callback(request):
    authority = request.GET.get("Authority") or request.GET.get("authority")
    payment = get_object_or_404(Payment, authority=authority) if authority else None

    if payment is None:
        return render(request, "payments/result.html", {"ok": False, "payment": None})

    ok = verify_payment(payment, request.GET.dict())
    return render(
        request,
        "payments/result.html",
        {"ok": ok, "payment": payment, "payable": payment.payable},
    )
