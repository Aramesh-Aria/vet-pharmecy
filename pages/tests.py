import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_home_page_renders_rtl():
    from django.test import Client

    response = Client().get(reverse("pages:home"))
    assert response.status_code == 200
    assert 'lang="fa"' in response.content.decode()
    assert 'dir="rtl"' in response.content.decode()


@pytest.mark.django_db
def test_login_page_renders():
    from django.test import Client

    response = Client().get(reverse("accounts:login"))
    assert response.status_code == 200
