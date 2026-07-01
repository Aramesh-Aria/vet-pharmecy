"""Appointment — an Owner's request for a visit and the visit Staff confirm
from it (CONTEXT.md). One model carries the whole lifecycle via ``status``.

Two flavours are designed for: an in-person **Service** appointment (animal +
service + preferred time, Staff confirm, pay later) and a paid **Online Visit**
(``is_online=True``, no Animal). Online Visit ships in Phase 5 with the gateway;
at this phase only the in-person Service path is built, but the field is here so
the model doesn't need reshaping later (ADR-0005).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Appointment(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", _("درخواست‌شده")
        CONFIRMED = "confirmed", _("تأییدشده")
        COMPLETED = "completed", _("انجام‌شده")
        CANCELLED = "cancelled", _("لغوشده")
        NO_SHOW = "no_show", _("عدم مراجعه")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name=_("مشتری"),
    )
    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
        verbose_name=_("حیوان"),
    )
    # Livestock appointments (farm visits) target a Herd instead of an Animal.
    herd = models.ForeignKey(
        "animals.Herd",
        on_delete=models.CASCADE,
        related_name="appointments",
        null=True,
        blank=True,
        verbose_name=_("گله"),
    )
    service = models.ForeignKey(
        "catalog.Service",
        on_delete=models.PROTECT,
        related_name="appointments",
        null=True,
        blank=True,
        verbose_name=_("خدمت"),
    )
    is_online = models.BooleanField(_("ویزیت آنلاین"), default=False)

    preferred_date = models.DateField(_("تاریخ پیشنهادی"))
    preferred_time_note = models.CharField(
        _("بازهٔ زمانی پیشنهادی"), max_length=100, blank=True,
        help_text=_("مثلاً «صبح» یا «بعدازظهر»"),
    )
    owner_note = models.TextField(_("توضیح مشتری"), blank=True)

    confirmed_datetime = models.DateTimeField(_("زمان تأییدشده"), null=True, blank=True)
    vet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="vet_appointments",
        null=True,
        blank=True,
        verbose_name=_("دامپزشک"),
    )
    staff_note = models.TextField(_("یادداشت همکار"), blank=True)
    status = models.CharField(
        _("وضعیت"), max_length=12, choices=Status.choices, default=Status.REQUESTED
    )
    created_at = models.DateTimeField(_("ثبت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("به‌روزرسانی"), auto_now=True)

    class Meta:
        verbose_name = _("نوبت")
        verbose_name_plural = _("نوبت‌ها")
        ordering = ["-created_at"]

    def __str__(self):
        return f"نوبت #{self.pk}"

    @property
    def subject(self):
        """The Animal or Herd this appointment is for."""
        return self.animal or self.herd

    @property
    def subject_category_id(self):
        subject = self.subject
        return subject.animal_category_id if subject else None

    def clean(self):
        # In-person Service appointments need a subject (Animal or Herd) + service.
        if not self.is_online:
            if self.animal_id is None and self.herd_id is None:
                raise ValidationError(
                    {"animal": _("برای خدمت حضوری، انتخاب حیوان یا گله لازم است.")}
                )
            if self.animal_id and self.herd_id:
                raise ValidationError(_("همزمان حیوان و گله قابل انتخاب نیست."))
            if self.service_id is None:
                raise ValidationError({"service": _("انتخاب خدمت لازم است.")})
            # The service must belong to the subject's Animal Category.
            if self.service_id and self.subject_category_id and (
                self.service.animal_category_id != self.subject_category_id
            ):
                raise ValidationError(
                    {"service": _("این خدمت با دستهٔ انتخاب‌شده همخوانی ندارد.")}
                )

    def get_absolute_url(self):
        return reverse("appointments:detail", kwargs={"pk": self.pk})

    @property
    def is_cancellable(self) -> bool:
        return self.status in {self.Status.REQUESTED, self.Status.CONFIRMED}
