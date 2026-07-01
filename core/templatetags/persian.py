"""Template filters for Farsi/RTL presentation (ADR-0002).

Dates are stored as standard datetimes and rendered Jalali on the way out;
numbers and prices render with Persian digits and thousands separators.
"""
import datetime

import jdatetime
from django import template

register = template.Library()

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_FA_THOUSANDS = "٬"  # Arabic/Persian thousands separator «٬»


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
    """Format a Rial amount with thousands separators and Persian digits.

    Groups in threes with the Persian thousands separator «٬» (e.g. ۵٬۰۰۰٬۰۰۰),
    independent of Django's NUMBER_GROUPING setting.
    """
    if value is None or value == "":
        return ""
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    sign = "-" if number < 0 else ""
    grouped = f"{abs(number):,}".replace(",", _FA_THOUSANDS)
    return (sign + grouped).translate(_EN_TO_FA)
