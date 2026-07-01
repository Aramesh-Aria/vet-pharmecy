from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

from catalog.models import AnimalCategory

from .forms import ContactForm
from .models import Practice


class HomeView(TemplateView):
    """Public home page: one tile per active Animal Category (ADR-0006)."""

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = AnimalCategory.objects.filter(is_active=True)
        return ctx


def contact(request):
    """Business contact/location page + a simple message form (CONTEXT.md).
    Accurate contact info here is required for e-Namad (ADR-0005)."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "پیام شما دریافت شد. به‌زودی با شما تماس می‌گیریم.")
            return redirect("pages:contact")
    else:
        form = ContactForm()
    return render(request, "pages/contact.html", {"form": form})


class AboutView(TemplateView):
    template_name = "pages/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["practice"] = Practice.get()
        return ctx


class TermsView(TemplateView):
    template_name = "pages/terms.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["practice"] = Practice.get()
        return ctx


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /shop/",
        "Disallow: /clinic/",
        "Disallow: /animals/",
        "Disallow: /payments/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@cache_control(max_age=60)
def healthz(request):
    """Lightweight liveness/readiness probe: confirms the DB answers."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return HttpResponse("db error", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")
