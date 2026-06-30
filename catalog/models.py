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

    @classmethod
    def product_sections(cls):
        """Sections whose contents are physical Products (the store)."""
        return (cls.MEDICATION, cls.EQUIPMENT)


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


class Product(ImageProcessingMixin, models.Model):
    """A physical item the pharmacy/store sells: a Medication or Equipment
    (CONTEXT.md). Every Product carries an Animal Category and a (product)
    Section, so it slots into the category-first navigation (ADR-0006).

    Prices are stored as integer Rial (the settlement currency, ADR-0005).
    """

    image_specs = {"image": {"fit": (800, 800)}}

    animal_category = models.ForeignKey(
        AnimalCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("دستهٔ حیوان"),
    )
    section = models.CharField(
        _("بخش"),
        max_length=20,
        choices=[(s.value, s.label) for s in Section.product_sections()],
    )
    name = models.CharField(_("نام"), max_length=200)
    slug = models.SlugField(_("نامک"), max_length=200, unique=True)
    description = models.TextField(_("توضیح"), blank=True)
    price = models.PositiveBigIntegerField(_("قیمت (ریال)"))
    stock = models.PositiveIntegerField(_("موجودی"), default=0)
    image = models.ImageField(_("تصویر"), upload_to="products/", blank=True)
    is_prescription_only = models.BooleanField(
        _("فقط با نسخه"),
        default=False,
        help_text=_("فقط برای داروها؛ بدون نسخهٔ معتبر قابل سفارش نیست."),
    )
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("ایجاد"), auto_now_add=True)

    class Meta:
        verbose_name = _("کالا")
        verbose_name_plural = _("کالاها")
        ordering = ["name"]
        indexes = [models.Index(fields=["animal_category", "section", "is_active"])]

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.section not in Section.values:
            raise ValidationError({"section": _("بخش نامعتبر است.")})
        if self.is_prescription_only and self.section != Section.MEDICATION:
            raise ValidationError(
                {"is_prescription_only": _("فقط داروها می‌توانند «فقط با نسخه» باشند.")}
            )

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def orderable(self) -> bool:
        """Can an Owner add this straight to the cart? Prescription-only meds go
        through the Prescription/Refill flow instead (ADR-0005)."""
        return self.is_active and self.in_stock and not self.is_prescription_only

    def get_absolute_url(self):
        return reverse(
            "catalog:product",
            kwargs={
                "slug": self.animal_category.slug,
                "section": self.section,
                "product_slug": self.slug,
            },
        )


class Service(models.Model):
    """An in-person offering the clinic performs for an Animal (CONTEXT.md) —
    a procedure or treatment, booked via an Appointment and paid later. Lives in
    the Service section of its Animal Category (ADR-0006)."""

    animal_category = models.ForeignKey(
        AnimalCategory,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name=_("دستهٔ حیوان"),
    )
    name = models.CharField(_("نام"), max_length=200)
    slug = models.SlugField(_("نامک"), max_length=200, unique=True)
    description = models.TextField(_("توضیح"), blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        _("مدت تقریبی (دقیقه)"), null=True, blank=True
    )
    price = models.PositiveBigIntegerField(_("قیمت تقریبی (ریال)"), null=True, blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)

    class Meta:
        verbose_name = _("خدمت")
        verbose_name_plural = _("خدمات")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:section", kwargs={
            "slug": self.animal_category.slug, "section": Section.SERVICE,
        })
