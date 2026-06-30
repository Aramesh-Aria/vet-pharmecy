"""Template filters for Farsi/RTL presentation (ADR-0002).

Dates are stored as standard datetimes and rendered Jalali on the way out;
numbers and prices render with Persian digits and thousands separators.
"""
import datetime

import jdatetime
from django import template
from django.utils.formats import number_format

register = template.Library()

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter(name="fa_digits")
def fa_digits(value):
    """Convert ASCII digits in *value* to Persian digits."""
    if value is None:
        return ""
    return str(value).translate(_EN_TO_FA)


@register.filter(name="jalali")
def jalali(value, fmt="%Y/%m/%d"):
    """Render a date/datetime in the Jalali calendar with Persian digits."""
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        jd = jdatetime.datetime.fromgregorian(datetime=value)
    elif isinstance(value, datetime.date):
        jd = jdatetime.date.fromgregorian(date=value)
    else:
        return value
    return jd.strftime(fmt).translate(_EN_TO_FA)


@register.filter(name="toman")
def toman(value):
    """Format a Rial/Toman amount with thousands separators and Persian digits."""
    if value is None or value == "":
        return ""
    try:
        formatted = number_format(value, decimal_pos=0, use_l10n=False, force_grouping=True)
    except (TypeError, ValueError):
        return value
    return formatted.translate(_EN_TO_FA)
