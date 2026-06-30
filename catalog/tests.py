import pytest
from django.test import Client
from django.urls import reverse

from catalog.models import AnimalCategory, Product, Section


@pytest.mark.django_db
def test_four_categories_seeded():
    slugs = set(AnimalCategory.objects.values_list("slug", flat=True))
    assert {"ornamental-birds", "companion-pets", "equine", "ruminants"} <= slugs


@pytest.mark.django_db
def test_home_shows_category_tiles():
    from django.test import Client

    resp = Client().get(reverse("pages:home"))
    assert resp.status_code == 200
    assert "حیوانات خانگی" in resp.content.decode()


@pytest.mark.django_db
def test_category_landing_lists_four_sections():
    from django.test import Client

    resp = Client().get(reverse("catalog:category", args=["companion-pets"]))
    assert resp.status_code == 200
    body = resp.content.decode()
    for _, label in Section.choices:
        assert str(label) in body


@pytest.mark.django_db
def test_section_page_ok_and_bad_section_404():
    from django.test import Client

    ok = Client().get(reverse("catalog:section", args=["companion-pets", "medication"]))
    assert ok.status_code == 200

    bad = Client().get("/c/companion-pets/nonsense/")
    assert bad.status_code == 404


@pytest.mark.django_db
def test_inactive_category_not_listed_or_reachable():
    AnimalCategory.objects.filter(slug="equine").update(is_active=False)
    home = Client().get(reverse("pages:home")).content.decode()
    assert "اسب" not in home
    assert Client().get(reverse("catalog:category", args=["equine"])).status_code == 404


@pytest.mark.django_db
def test_medication_section_lists_active_products():
    cat = AnimalCategory.objects.get(slug="companion-pets")
    Product.objects.create(
        animal_category=cat, section=Section.MEDICATION, name="ویتامین",
        slug="vitamin", price=300_000, stock=5,
    )
    Product.objects.create(
        animal_category=cat, section=Section.MEDICATION, name="پنهان",
        slug="hidden", price=100_000, stock=5, is_active=False,
    )
    body = Client().get(reverse("catalog:section", args=["companion-pets", "medication"])).content.decode()
    assert "ویتامین" in body
    assert "پنهان" not in body


@pytest.mark.django_db
def test_product_detail_renders_and_filters_by_category_section():
    cat = AnimalCategory.objects.get(slug="companion-pets")
    p = Product.objects.create(
        animal_category=cat, section=Section.EQUIPMENT, name="قلاده",
        slug="leash", price=450_000, stock=3,
    )
    ok = Client().get(p.get_absolute_url())
    assert ok.status_code == 200
    assert "قلاده" in ok.content.decode()
    # Wrong section in the URL must not resolve to the product.
    bad = Client().get(reverse("catalog:product", args=["companion-pets", "medication", "leash"]))
    assert bad.status_code == 404


@pytest.mark.django_db
def test_search_filter_narrows_products():
    cat = AnimalCategory.objects.get(slug="companion-pets")
    for name, slug in [("شامپو", "shampoo"), ("برس", "brush")]:
        Product.objects.create(
            animal_category=cat, section=Section.EQUIPMENT, name=name,
            slug=slug, price=200_000, stock=5,
        )
    url = reverse("catalog:section", args=["companion-pets", "equipment"])
    body = Client().get(url, {"q": "شامپو"}).content.decode()
    assert "شامپو" in body
    assert "برس" not in body
