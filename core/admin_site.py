"""Customised admin site with an operational dashboard (PLAN §2 — Staff use the
Django admin now; a bespoke staff dashboard comes later).

Django's admin is already Farsi + RTL because LANGUAGE_CODE='fa'. This adds a
landing dashboard with the daily work queues — pending appointment requests,
orders to process, refills to price, and vaccinations coming due — so staff see
what needs action without hunting through changelists.
"""
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class VetAdminSite(AdminSite):
    site_header = _("مدیریت کلینیک و داروخانه دامپزشکی")
    site_title = _("مدیریت دامپزشکی")
    index_title = _("داشبورد")
    index_template = "admin/dashboard_index.html"

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
