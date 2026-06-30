"""Lightweight clinical records (PLAN §2): a Visit Record per completed
appointment, and Vaccinations that drive due-date reminders. Not a full EMR —
labs, attachments, and SOAP notes are explicitly out of scope (PLAN §9).
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class VisitRecord(models.Model):
    """The clinical note attached to a completed visit: date, offering, and the
    vet's notes. An Animal's visit history is its list of Visit Records."""

    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        related_name="visit_records",
        verbose_name=_("حیوان"),
    )
    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.SET_NULL,
        related_name="visit_records",
        null=True,
        blank=True,
        verbose_name=_("نوبت"),
    )
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.SET_NULL,
        related_name="visit_records",
        null=True,
        blank=True,
        verbose_name=_("خدمت"),
    )
    date = models.DateField(_("تاریخ"))
    vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="visit_records",
        null=True,
        blank=True,
        verbose_name=_("دامپزشک"),
    )
    notes = models.TextField(_("شرح و توضیحات"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("پروندهٔ ویزیت")
        verbose_name_plural = _("پرونده‌های ویزیت")
        ordering = ["-date"]

    def __str__(self):
        return f"ویزیت {self.animal} در {self.date}"


class Vaccination(models.Model):
    """A record that an Animal received a vaccine on a date, with an optional
    next-due date that drives reminders (CONTEXT.md)."""

    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        related_name="vaccinations",
        verbose_name=_("حیوان"),
    )
    vaccine_name = models.CharField(_("نام واکسن"), max_length=150)
    date_given = models.DateField(_("تاریخ تزریق"))
    next_due = models.DateField(_("تاریخ نوبت بعدی"), null=True, blank=True)
    notes = models.TextField(_("توضیحات"), blank=True)
    # Set when a due-date reminder has been sent, so the job doesn't repeat it.
    reminded_at = models.DateTimeField(_("زمان یادآوری"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("واکسیناسیون")
        verbose_name_plural = _("واکسیناسیون‌ها")
        ordering = ["-date_given"]

    def __str__(self):
        return f"{self.vaccine_name} — {self.animal}"
