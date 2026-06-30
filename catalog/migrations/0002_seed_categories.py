"""Seed the four starting Animal Categories (ADR-0006, CONTEXT.md).

Categories are Staff-editable afterwards; this only provides sensible defaults
so the home page has tiles out of the box.
"""
from django.db import migrations

CATEGORIES = [
    {"name": "پرندگان زینتی", "slug": "ornamental-birds", "order": 1},
    {"name": "حیوانات خانگی", "slug": "companion-pets", "order": 2},
    {"name": "اسب", "slug": "equine", "order": 3},
    {"name": "نشخوارکنندگان", "slug": "ruminants", "order": 4},
]


def seed(apps, schema_editor):
    AnimalCategory = apps.get_model("catalog", "AnimalCategory")
    for data in CATEGORIES:
        AnimalCategory.objects.update_or_create(slug=data["slug"], defaults=data)


def unseed(apps, schema_editor):
    AnimalCategory = apps.get_model("catalog", "AnimalCategory")
    AnimalCategory.objects.filter(
        slug__in=[c["slug"] for c in CATEGORIES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
