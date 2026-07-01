"""Public-content models: the Practice business identity and contact messages.

``Practice`` is the single business that owns the site (CONTEXT.md) — a singleton
holding the global identity (name, contact, hours, address, terms) that drives
the footer, the Contact/Terms/About pages, and SEO. Accurate business-identity
content here is a prerequisite for the e-Namad application (ADR-0005).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Practice(models.Model):
    name = models.CharField(_("نام"), max_length=150, default="دامپزشکی هیرکان")
    tagline = models.CharField(
        _("شعار"), max_length=255, blank=True,
        default="درمانگاه و داروخانهٔ دامپزشکی در آمل و مازندران",
    )
    phone = models.CharField(_("تلفن ثابت"), max_length=30, blank=True)
    mobile = models.CharField(_("تلفن همراه"), max_length=30, blank=True)
    email = models.EmailField(_("ایمیل"), blank=True)

    province = models.CharField(_("استان"), max_length=30, blank=True, default="مازندران")
    city = models.CharField(_("شهر"), max_length=80, blank=True, default="آمل")
    address = models.TextField(_("نشانی"), blank=True)
    postal_code = models.CharField(_("کد پستی"), max_length=10, blank=True)
    hours = models.CharField(
        _("ساعات کاری"), max_length=255, blank=True,
        default="هر روز ۹ تا ۲۰ — جمعه‌ها تا ۱۴",
    )
    map_embed_url = models.URLField(
        _("لینک نقشه"), blank=True,
        help_text=_("لینک نقشهٔ نشان یا گوگل برای نمایش موقعیت."),
    )

    about = models.TextField(_("دربارهٔ ما"), blank=True)
    terms = models.TextField(
        _("قوانین و مقررات"), blank=True,
        help_text=_("متن قوانین و مقررات — برای نماد اعتماد الکترونیک لازم است."),
    )

    instagram = models.URLField(_("اینستاگرام"), blank=True)
    telegram = models.URLField(_("تلگرام"), blank=True)
    enamad_html = models.TextField(
        _("کد نماد اعتماد الکترونیک"), blank=True,
        help_text=_("کد HTML نماد؛ پس از دریافت e-Namad وارد شود."),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("مشخصات کسب‌وکار")
        verbose_name_plural = _("مشخصات کسب‌وکار")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce a single row (singleton)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # the singleton is never deleted

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    """A message sent through the public contact form. Staff triage in admin."""

    name = models.CharField(_("نام"), max_length=150)
    phone = models.CharField(_("شماره تماس"), max_length=15)
    message = models.TextField(_("پیام"))
    is_handled = models.BooleanField(_("رسیدگی‌شده"), default=False)
    created_at = models.DateTimeField(_("زمان ارسال"), auto_now_add=True)

    class Meta:
        verbose_name = _("پیام تماس")
        verbose_name_plural = _("پیام‌های تماس")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.created_at:%Y-%m-%d}"
