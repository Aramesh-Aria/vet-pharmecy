"""Seed demo catalog content (Products + Services) for testing a deployment.

Idempotent (keyed on slug) and **creates no users** — no customers, no superuser.
Run after migrate on a fresh deployment::

    python manage.py seed_data

The four Animal Categories are already created by a catalog data migration; this
fills them with browsable products and services so the site isn't empty.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import AnimalCategory, Product, Service

# Per-category demo content. Prices are in Rial.
PRODUCTS = {
    "ornamental-birds": [
        ("مولتی‌ویتامین پرندگان", "medication", 850_000, 40, False),
        ("آنتی‌بیوتیک مخصوص پرندگان", "medication", 1_250_000, 15, True),
        ("قفس استاندارد پرندگان زینتی", "equipment", 3_500_000, 8, False),
        ("ظرف آب و دان اتوماتیک", "equipment", 650_000, 25, False),
    ],
    "companion-pets": [
        ("غذای خشک گربه (۲ کیلوگرم)", "medication", 1_900_000, 50, False),
        ("قرص ضدانگل سگ و گربه", "medication", 480_000, 60, False),
        ("آنتی‌بیوتیک دامپزشکی (نسخه‌ای)", "medication", 2_100_000, 12, True),
        ("قلاده و بند چرمی", "equipment", 950_000, 30, False),
        ("جعبهٔ حمل حیوان خانگی", "equipment", 2_400_000, 10, False),
    ],
    "equine": [
        ("مکمل معدنی اسب", "medication", 3_200_000, 20, False),
        ("پمادِ ترمیم‌کنندهٔ سُم", "medication", 1_450_000, 18, False),
        ("افسار و زین چرمی", "equipment", 8_900_000, 5, False),
        ("برس و قشوی اسب", "equipment", 720_000, 22, False),
    ],
    "ruminants": [
        ("واکسن تب برفکی (دامی)", "medication", 1_100_000, 35, True),
        ("داروی ضدانگل دام (بطری)", "medication", 1_650_000, 28, False),
        ("شیردوش برقی", "equipment", 12_500_000, 4, False),
        ("سطل و تجهیزات تغذیهٔ دام", "equipment", 540_000, 40, False),
    ],
}

SERVICES = {
    "ornamental-birds": [
        ("معاینهٔ عمومی پرنده", 30, 800_000),
        ("ناخن و منقار", 20, 400_000),
    ],
    "companion-pets": [
        ("معاینهٔ سلامت سگ و گربه", 30, 900_000),
        ("واکسیناسیون سالانه", 20, 1_200_000),
        ("جراحی و عقیم‌سازی", 90, 6_500_000),
    ],
    "equine": [
        ("معاینهٔ دوره‌ای اسب", 45, 2_500_000),
        ("مراقبت و درمان سُم", 60, 1_800_000),
    ],
    "ruminants": [
        ("ویزیت مزرعه و گله", 60, 3_000_000),
        ("واکسیناسیون گله‌ای", 120, 4_500_000),
    ],
}


def _slugify(category_slug: str, name: str, idx: int) -> str:
    # Names are Persian; build a stable ASCII slug from category + index.
    return f"{category_slug}-{idx}"


class Command(BaseCommand):
    help = "ایجاد دادهٔ نمونهٔ فروشگاه و خدمات برای آزمایش (بدون کاربر)"

    @transaction.atomic
    def handle(self, *args, **options):
        products = services = 0

        for slug, items in PRODUCTS.items():
            category = AnimalCategory.objects.filter(slug=slug).first()
            if category is None:
                self.stdout.write(self.style.WARNING(f"دستهٔ «{slug}» یافت نشد؛ رد شد."))
                continue
            for idx, (name, section, price, stock, rx_only) in enumerate(items, 1):
                _, created = Product.objects.get_or_create(
                    slug=_slugify(slug, name, idx),
                    defaults={
                        "animal_category": category,
                        "section": section,
                        "name": name,
                        "price": price,
                        "stock": stock,
                        "is_prescription_only": rx_only,
                        "description": f"{name} — کالای نمونه برای آزمایش.",
                    },
                )
                products += int(created)

        for slug, items in SERVICES.items():
            category = AnimalCategory.objects.filter(slug=slug).first()
            if category is None:
                continue
            for idx, (name, duration, price) in enumerate(items, 1):
                _, created = Service.objects.get_or_create(
                    slug=f"svc-{slug}-{idx}",
                    defaults={
                        "animal_category": category,
                        "name": name,
                        "duration_minutes": duration,
                        "price": price,
                        "description": f"{name} — خدمت نمونه برای آزمایش.",
                    },
                )
                services += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"دادهٔ نمونه ساخته شد: {products} کالا و {services} خدمت "
                f"(بدون هیچ کاربر/مشتری/مدیر)."
            )
        )
