"""Form widgets for Farsi/RTL input.

JalaliDateInput lets the user see and pick a **Jalali (Shamsi)** date while the
form still submits a Gregorian ISO string — so model ``DateField``s store
Gregorian unchanged (ADR-0002). The calendar UI is added by
``static/js/jdatepicker.js``; without JS the hidden ISO field still works.
"""
import datetime

import jdatetime
from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


class JalaliDateInput(forms.DateInput):
    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%d")

    def render(self, name, value, attrs=None, renderer=None):
        date = None
        if isinstance(value, datetime.date):
            date = value
        elif isinstance(value, str) and value:
            try:
                date = datetime.date.fromisoformat(value)
            except ValueError:
                date = None

        iso = date.isoformat() if date else ""
        display = ""
        if date:
            jd = jdatetime.date.fromgregorian(date=date)
            display = jd.strftime("%Y/%m/%d").translate(_EN_TO_FA)

        field_id = (attrs or {}).get("id") or f"id_{name}"
        return format_html(
            '<div class="jdate" data-jdate>'
            '<input type="text" class="input jdate__display" id="{id}" value="{disp}" '
            'placeholder="انتخاب تاریخ" autocomplete="off" readonly aria-haspopup="dialog">'
            '<input type="hidden" name="{name}" class="jdate__value" value="{iso}">'
            '<button type="button" class="jdate__icon" tabindex="-1" aria-label="باز کردن تقویم">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7"><rect x="3" y="5" width="18" height="16" rx="2"/>'
            '<path d="M3 9h18M8 3v4M16 3v4"/></svg></button>'
            "</div>",
            id=field_id,
            disp=display,
            name=name,
            iso=iso,
        )


class CategoryDataSelect(forms.Select):
    """A ``<select>`` that tags each option with ``data-category`` so JS can
    filter options to a chosen Animal Category. Used in the prescription admin
    (medications for the pet's category) and the appointment form (services for
    the subject's category). Keyed by the option value as a string, so it works
    with model PKs and composite values like ``animal:5`` alike."""

    def __init__(self, attrs=None, choices=(), category_by_value=None):
        super().__init__(attrs, choices)
        self.category_by_value = {
            str(k): v for k, v in (category_by_value or {}).items()
        }

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        key = str(getattr(value, "value", value))  # unwrap ModelChoiceIteratorValue
        if key in self.category_by_value:
            option["attrs"]["data-category"] = self.category_by_value[key]
        return option


class JalaliSplitDateTimeWidget(forms.Widget):
    """A Jalali date picker + a native time input, for editing a DateTimeField
    in the admin. The date half reuses JalaliDateInput (submits Gregorian ISO),
    the time half a native ``<input type=time>``; the field recombines them."""

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.date_widget = JalaliDateInput()

    def render(self, name, value, attrs=None, renderer=None):
        date_val, time_val = None, ""
        if isinstance(value, (list, tuple)):
            date_val, time_val = value[0], value[1] or ""
        elif isinstance(value, datetime.datetime):
            date_val, time_val = value.date(), value.strftime("%H:%M")

        date_html = self.date_widget.render(f"{name}_0", date_val, {"id": f"id_{name}"})
        return format_html(
            '<div class="jdatetime">{date}'
            '<input type="time" name="{name}_1" value="{time}" class="input jdatetime__time" '
            'id="id_{name}_1" aria-label="ساعت"></div>',
            date=mark_safe(date_html),
            name=name,
            time=time_val,
        )

    def value_from_datadict(self, data, files, name):
        return [
            self.date_widget.value_from_datadict(data, files, f"{name}_0"),
            data.get(f"{name}_1", ""),
        ]


class JalaliSplitDateTimeField(forms.MultiValueField):
    """Pairs with :class:`JalaliSplitDateTimeWidget`. Cleans the Gregorian date
    + time and combines them into a ``datetime``."""

    widget = JalaliSplitDateTimeWidget

    def __init__(self, **kwargs):
        fields = (forms.DateField(), forms.TimeField())
        super().__init__(fields, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        if data_list and data_list[0] and data_list[1]:
            return datetime.datetime.combine(data_list[0], data_list[1])
        return None


class PrettyImageInput(forms.ClearableFileInput):
    """A friendlier image upload: a styled drop-button, a thumbnail of the
    current image, and a clear «حذف تصویر» toggle — instead of the browser's
    raw file input. Enhanced by static/js/app.js (filename + live preview)."""

    def render(self, name, value, attrs=None, renderer=None):
        ctx = self.get_context(name, value, attrs)["widget"]
        is_initial = ctx["is_initial"]
        file_attrs = mark_safe(flatatt(ctx["attrs"]))
        cta = "انتخاب تصویر جدید" if is_initial else "انتخاب تصویر"

        pieces = ['<div class="filefield" data-filefield>']
        if is_initial:
            url = value.url
            fname = url.rsplit("/", 1)[-1]
            clear = ""
            if not self.is_required and ctx.get("checkbox_name"):
                clear = format_html(
                    '<label class="filefield__clear"><input type="checkbox" '
                    'name="{}" id="{}"><span>حذف تصویر</span></label>',
                    ctx["checkbox_name"], ctx["checkbox_id"],
                )
            pieces.append(format_html(
                '<div class="filefield__current">'
                '<img class="filefield__thumb" src="{}" alt="" data-preview>'
                '<div class="filefield__cur"><span class="filefield__cur-name">{}</span>{}</div>'
                "</div>",
                url, fname, clear,
            ))
        else:
            pieces.append(
                '<img class="filefield__thumb" alt="" data-preview hidden>'
            )

        pieces.append(format_html(
            '<label class="filefield__drop">'
            '<input type="file" name="{}" accept="image/*" class="filefield__input"{}>'
            '<svg class="filefield__icon" width="22" height="22" viewBox="0 0 24 24" '
            'fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 15V4"/>'
            '<path d="M8 8l4-4 4 4"/><path d="M4 14v3a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-3"/></svg>'
            '<span class="filefield__cta">{}</span>'
            '<span class="filefield__name" data-filename>یک فایل تصویری انتخاب کنید</span>'
            "</label>",
            name, file_attrs, cta,
        ))
        pieces.append("</div>")
        return mark_safe("".join(pieces))
