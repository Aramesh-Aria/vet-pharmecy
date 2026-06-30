"""Iranian mobile phone number validation and normalisation.

Phone is the account identity (ADR-0004), so it must be stored in one canonical
form. We canonicalise to the national ``09XXXXXXXXX`` shape (11 digits) and
accept the common ways users type it: with +98, 0098, or a leading 98.
"""
import re

from django.core.exceptions import ValidationError

# Iranian mobile numbers: operator prefix 9 followed by 9 digits -> 09XXXXXXXXX.
_CANONICAL_RE = re.compile(r"^09\d{9}$")


def normalize_phone(value: str) -> str:
    """Return the canonical ``09XXXXXXXXX`` form, or raise ValidationError."""
    if value is None:
        raise ValidationError("شماره موبایل لازم است.")

    # Strip spaces, dashes, parentheses and convert Persian/Arabic digits.
    digits = _to_ascii_digits(str(value)).strip()
    digits = re.sub(r"[\s\-()]", "", digits)

    # Normalise international prefixes to the national 0-prefixed form.
    if digits.startswith("+98"):
        digits = "0" + digits[3:]
    elif digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits

    if not _CANONICAL_RE.match(digits):
        raise ValidationError("شماره موبایل معتبر نیست. نمونه: ۰۹۱۲۳۴۵۶۷۸۹")
    return digits


def validate_phone(value: str) -> None:
    """Model/field validator wrapper around :func:`normalize_phone`."""
    normalize_phone(value)


# Persian (۰-۹) and Arabic-Indic (٠-٩) digits -> ASCII.
_DIGIT_MAP = {ord(p): str(i) for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}
_DIGIT_MAP.update({ord(a): str(i) for i, a in enumerate("٠١٢٣٤٥٦٧٨٩")})


def _to_ascii_digits(value: str) -> str:
    return value.translate(_DIGIT_MAP)
