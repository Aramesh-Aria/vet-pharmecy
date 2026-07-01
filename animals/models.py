"""Animal and Herd — the units of care (CONTEXT.md).

Companion pets and equine are tracked as individual :class:`Animal` records.
Livestock (Ruminants) use a lighter :class:`Herd` record (species, head-count,
farm location) instead of one row per head — the hybrid model from PLAN §10.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.images import ImageProcessingMixin


class Sex(models.TextChoices):
    MALE = "male", _("نر")
    FEMALE = "female", _("ماده")
    UNKNOWN = "unknown", _("نامشخص")


class Animal(ImageProcessingMixin, models.Model):
    """An individual animal belonging to an Owner (companion pets / equine)."""

    # Photos shrink to fit within 1200×1200, keeping aspect ratio.
    image_specs = {"photo": {"max_size": (1200, 1200)}}

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="animals",
        verbose_name=_("مشتری"),
    )
    animal_category = models.ForeignKey(
        "catalog.AnimalCategory",
        on_delete=models.PROTECT,
        related_name="animals",
        verbose_name=_("دستهٔ حیوان"),
    )
    name = models.CharField(_("نام"), max_length=100)
    species = models.CharField(
        _("گونه"), max_length=50, help_text=_("مثلاً گربه، سگ، اسب")
    )
    sex = models.CharField(
        _("جنسیت"), max_length=10, choices=Sex.choices, default=Sex.UNKNOWN
    )
    birth_date = models.DateField(_("تاریخ تولد"), null=True, blank=True)
    weight_kg = models.DecimalField(
        _("وزن (کیلوگرم)"), max_digits=6, decimal_places=2, null=True, blank=True
    )
    photo = models.ImageField(_("عکس"), upload_to="animals/", blank=True)
    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)

    class Meta:
        verbose_name = _("حیوان")
        verbose_name_plural = _("حیوانات")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("animals:detail", kwargs={"pk": self.pk})


class Herd(models.Model):
    """A livestock group record (Ruminants) — population-level unit of care."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="herds",
        verbose_name=_("مشتری"),
    )
    animal_category = models.ForeignKey(
        "catalog.AnimalCategory",
        on_delete=models.PROTECT,
        related_name="herds",
        verbose_name=_("دستهٔ حیوان"),
    )
    name = models.CharField(
        _("عنوان گله"), max_length=100, blank=True,
        help_text=_("یک نام برای شناسایی گله، مثلاً «گلهٔ گوسفند شمالی»"),
    )
    species = models.CharField(
        _("گونه"), max_length=50, help_text=_("مثلاً گوسفند، بز، شتر")
    )
    head_count = models.PositiveIntegerField(_("تعداد رأس"), default=1)
    farm_location = models.CharField(_("موقعیت دامداری"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)

    class Meta:
        verbose_name = _("گله")
        verbose_name_plural = _("گله‌ها")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"{self.species} ({self.head_count} رأس)"

    def get_absolute_url(self):
        return reverse("animals:herd_detail", kwargs={"pk": self.pk})
