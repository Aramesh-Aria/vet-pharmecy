"""Admin mixin that renders Jalali (Shamsi) date pickers for date fields.

Staff see and pick Jalali dates in the admin; the widgets submit Gregorian, so
model ``DateField``/``DateTimeField``s are unchanged (no migration). Reuses the
site's own self-hosted picker (``jdatepicker.js``) plus a small, namespaced
admin stylesheet — no CDN, no jQuery dependency (ADR-0002).
"""
from django.db import models
from django.utils.text import capfirst

from .widgets import JalaliDateInput, JalaliSplitDateTimeField


class JalaliAdminMixin:
    class Media:
        css = {"all": ["css/admin_jalali.css"]}
        js = ["js/jdatepicker.js"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        editable = not (getattr(db_field, "auto_now", False)
                        or getattr(db_field, "auto_now_add", False))

        # DateTimeField is a subclass of DateField, so check it first.
        if isinstance(db_field, models.DateTimeField) and editable:
            return JalaliSplitDateTimeField(
                required=not db_field.blank,
                label=capfirst(db_field.verbose_name),
                help_text=db_field.help_text,
            )

        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if (
            field is not None
            and editable
            and isinstance(db_field, models.DateField)
            and not isinstance(db_field, models.DateTimeField)
        ):
            field.widget = JalaliDateInput()
        return field
