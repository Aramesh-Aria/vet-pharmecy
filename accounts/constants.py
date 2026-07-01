"""Shared choice lists for accounts."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Province(models.TextChoices):
    """The 31 provinces of Iran. Stored as the Farsi name; used later to drive
    courier availability (same-province vs other-province, PLAN §9)."""

    AZARBAYJAN_SHARGHI = "آذربایجان شرقی", _("آذربایجان شرقی")
    AZARBAYJAN_GHARBI = "آذربایجان غربی", _("آذربایجان غربی")
    ARDABIL = "اردبیل", _("اردبیل")
    ESFAHAN = "اصفهان", _("اصفهان")
    ALBORZ = "البرز", _("البرز")
    ILAM = "ایلام", _("ایلام")
    BUSHEHR = "بوشهر", _("بوشهر")
    TEHRAN = "تهران", _("تهران")
    CHAHARMAHAL = "چهارمحال و بختیاری", _("چهارمحال و بختیاری")
    KHORASAN_JONUBI = "خراسان جنوبی", _("خراسان جنوبی")
    KHORASAN_RAZAVI = "خراسان رضوی", _("خراسان رضوی")
    KHORASAN_SHOMALI = "خراسان شمالی", _("خراسان شمالی")
    KHUZESTAN = "خوزستان", _("خوزستان")
    ZANJAN = "زنجان", _("زنجان")
    SEMNAN = "سمنان", _("سمنان")
    SISTAN = "سیستان و بلوچستان", _("سیستان و بلوچستان")
    FARS = "فارس", _("فارس")
    GHAZVIN = "قزوین", _("قزوین")
    GHOM = "قم", _("قم")
    KORDESTAN = "کردستان", _("کردستان")
    KERMAN = "کرمان", _("کرمان")
    KERMANSHAH = "کرمانشاه", _("کرمانشاه")
    KOHGILUYEH = "کهگیلویه و بویراحمد", _("کهگیلویه و بویراحمد")
    GOLESTAN = "گلستان", _("گلستان")
    GILAN = "گیلان", _("گیلان")
    LORESTAN = "لرستان", _("لرستان")
    MAZANDARAN = "مازندران", _("مازندران")
    MARKAZI = "مرکزی", _("مرکزی")
    HORMOZGAN = "هرمزگان", _("هرمزگان")
    HAMEDAN = "همدان", _("همدان")
    YAZD = "یزد", _("یزد")
