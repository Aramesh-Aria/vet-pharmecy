import pytest
from django.urls import reverse

from catalog.models import AnimalCategory, Section


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
    from django.test import Client

    AnimalCategory.objects.filter(slug="equine").update(is_active=False)
    home = Client().get(reverse("pages:home")).content.decode()
    assert "اسب" not in home
    assert Client().get(reverse("catalog:category", args=["equine"])).status_code == 404
