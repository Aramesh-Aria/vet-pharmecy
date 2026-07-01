"""Customised admin site with an operational dashboard (PLAN §2 — Staff use the
Django admin now; a bespoke staff dashboard comes later).

Django's admin is already Farsi + RTL because LANGUAGE_CODE='fa'. This adds a
landing dashboard with the daily work queues — pending appointment requests,
orders to process, refills to price, and vaccinations coming due — so staff see
what needs action without hunting through changelists.
"""
from django.contrib.admin import AdminSite
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class VetAutocompleteJsonView(AutocompleteJsonView):
    """Enrich admin autocomplete results. The autocomplete endpoint is
    site-level, so this is the one place that controls *all* autocomplete text.

    For Animals we append the owner (so staff can disambiguate same-named pets)
    and attach the animal's category id, which the prescription admin's JS uses
    to filter the medication dropdown to that pet's category."""

    def serialize_result(self, obj, to_field_name):
        result = super().serialize_result(obj, to_field_name)
        from animals.models import Animal

        if isinstance(obj, Animal):
            owner = obj.owner
            who = f"{owner.full_name} ({owner.phone})" if owner.full_name else owner.phone
            result["text"] = f"{obj.name} — {who}"
            result["category_id"] = obj.animal_category_id
        return result


# Workflow-oriented grouping for the admin index/sidebar, ordered by how often
# staff use each area (most-used first). Each entry is "app_label.ModelName".
ADMIN_SECTIONS = [
    ("درمانگاه", [
        "appointments.Appointment",
        "records.Vaccination",
        "records.VisitRecord",
        "pharmacy.Prescription",
    ]),
    ("داروخانه و سفارش‌ها", [
        "pharmacy.Order",
        "pharmacy.RefillRequest",
        "payments.Payment",
    ]),
    ("کاتالوگ و فروشگاه", [
        "catalog.Product",
        "catalog.Service",
        "catalog.AnimalCategory",
    ]),
    ("مشتریان و حیوانات", [
        "accounts.User",
        "animals.Animal",
        "animals.Herd",
        "accounts.OwnerProfile",
    ]),
    ("سیستم", [
        "pharmacy.Cart",
        "accounts.PhoneOTP",
        "auth.Group",
    ]),
]


class VetAdminSite(AdminSite):
    site_header = _("مدیریت کلینیک و داروخانه دامپزشکی")
    site_title = _("مدیریت دامپزشکی")
    index_title = _("داشبورد")
    index_template = "admin/dashboard_index.html"

    def autocomplete_view(self, request):
        return VetAutocompleteJsonView.as_view(admin_site=self)(request)

    def get_app_list(self, request, app_label=None):
        """Group models into workflow sections (drives the index + sidebar).

        When a single app is requested (its own page) we defer to the default.
        Any model not listed in a section falls into «سایر» so nothing hides.
        """
        if app_label:
            return super().get_app_list(request, app_label)

        app_dict = self._build_app_dict(request)
        lookup = {}
        for label, app in app_dict.items():
            for model in app["models"]:
                lookup[f"{label}.{model['object_name']}"] = model

        sections, used = [], set()
        for index, (title, keys) in enumerate(ADMIN_SECTIONS):
            models = [lookup[k] for k in keys if k in lookup]
            used.update(k for k in keys if k in lookup)
            if models:
                sections.append({
                    "name": title,
                    "app_label": f"section_{index}",
                    "app_url": "",
                    "has_module_perms": True,
                    "models": models,
                })

        leftover = [model for key, model in sorted(lookup.items()) if key not in used]
        if leftover:
            sections.append({
                "name": _("سایر"),
                "app_label": "section_other",
                "app_url": "",
                "has_module_perms": True,
                "models": leftover,
            })
        return sections

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["dashboard"] = self._dashboard_cards()
        return super().index(request, extra_context)

    def _dashboard_cards(self):
        # Imported here to avoid app-loading order issues.
        from appointments.models import Appointment
        from pharmacy.models import Order, RefillRequest
        from records.models import Vaccination

        horizon = timezone.localdate() + timezone.timedelta(days=7)
        return [
            {
                "label": _("درخواست‌های نوبت در انتظار"),
                "count": Appointment.objects.filter(
                    status=Appointment.Status.REQUESTED
                ).count(),
                "url": reverse("admin:appointments_appointment_changelist")
                + "?status__exact=requested",
            },
            {
                "label": _("سفارش‌های در انتظار پردازش"),
                "count": Order.objects.filter(status=Order.Status.PLACED).count(),
                "url": reverse("admin:pharmacy_order_changelist")
                + "?status__exact=placed",
            },
            {
                "label": _("درخواست‌های تکرار نسخه برای قیمت‌گذاری"),
                "count": RefillRequest.objects.filter(
                    status=RefillRequest.Status.REQUESTED
                ).count(),
                "url": reverse("admin:pharmacy_refillrequest_changelist")
                + "?status__exact=requested",
            },
            {
                "label": _("واکسیناسیون‌های نزدیک به موعد"),
                "count": Vaccination.objects.filter(
                    next_due__isnull=False, next_due__lte=horizon
                ).count(),
                "url": reverse("admin:records_vaccination_changelist"),
            },
        ]
