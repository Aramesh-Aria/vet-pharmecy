"""Catalog taxonomy: AnimalCategory and Section (ADR-0006).

The whole site is organised by Animal Category first, then Section within it.
Categories are data-driven (Staff-editable); Sections are a fixed set of four.
Products and Services (the contents of the Medication/Equipment/Service
sections) arrive in Phases 2-3.
"""
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.images import ImageProcessingMixin


class Section(models.TextChoices):
    """The four offerings shown on every category landing page (ADR-0006)."""

    ONLINE_VISIT = "online_visit", _("ویزیت آنلاین")
    MEDICATION = "medication", _("دارو")
    EQUIPMENT = "equipment", _("تجهیزات")
    SERVICE = "service", _("خدمات")


class AnimalCategory(ImageProcessingMixin, models.Model):
    """A top-level grouping (Ornamental Birds, Companion Pets, Equine,
    Ruminants). The home page renders one image tile per active category."""

    # Tiles are cropped to a uniform square so the home grid looks consistent.
    image_specs = {"image": {"fit": (600, 600)}}

    name = models.CharField(_("نام"), max_length=100, unique=True)
    slug = models.SlugField(_("نامک"), max_length=100, unique=True)
    description = models.TextField(_("توضیح"), blank=True)
    image = models.ImageField(
        _("تصویر کاشی"), upload_to="categories/", blank=True
    )
    order = models.PositiveSmallIntegerField(_("ترتیب"), default=0)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("دستهٔ حیوان")
        verbose_name_plural = _("دسته‌های حیوان")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})
