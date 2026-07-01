import pytest
from django.test import Client
from django.urls import reverse

from pages.models import ContactMessage, Practice


@pytest.mark.django_db
def test_practice_is_a_singleton():
    a = Practice.get()
    b = Practice.get()
    assert a.pk == b.pk == 1
    # A second save can't create a second row.
    Practice(name="دیگر").save()
    assert Practice.objects.count() == 1


@pytest.mark.django_db
def test_home_page_renders_rtl():
    resp = Client().get(reverse("pages:home"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert 'lang="fa"' in body and 'dir="rtl"' in body


@pytest.mark.django_db
def test_content_pages_render():
    client = Client()
    for name in ("pages:contact", "pages:about", "pages:terms"):
        assert client.get(reverse(name)).status_code == 200


@pytest.mark.django_db
def test_contact_form_creates_message():
    resp = Client().post(
        reverse("pages:contact"),
        {"name": "علی", "phone": "۰۹۱۲۳۴۵۶۷۸۹", "message": "سلام، سوالی داشتم."},
    )
    assert resp.status_code == 302
    msg = ContactMessage.objects.get()
    assert msg.phone == "09123456789"  # normalised
    assert msg.name == "علی"


@pytest.mark.django_db
def test_footer_shows_practice_name():
    practice = Practice.get()
    practice.name = "دامپزشکی آزمایشی"
    practice.save()
    body = Client().get(reverse("pages:home")).content.decode()
    assert "دامپزشکی آزمایشی" in body


@pytest.mark.django_db
def test_robots_txt():
    resp = Client().get("/robots.txt")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")
    body = resp.content.decode()
    assert "Sitemap:" in body
    assert "Disallow: /admin/" in body


@pytest.mark.django_db
def test_sitemap_lists_pages_and_categories():
    from catalog.models import AnimalCategory

    resp = Client().get("/sitemap.xml")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "/contact/" in body
    cat = AnimalCategory.objects.filter(is_active=True).first()
    assert cat.get_absolute_url() in body


@pytest.mark.django_db
def test_healthz_ok():
    resp = Client().get("/healthz")
    assert resp.status_code == 200
    assert resp.content == b"ok"
