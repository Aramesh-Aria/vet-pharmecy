import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from animals.models import Animal, Herd
from catalog.models import AnimalCategory


@pytest.fixture
def owner(db):
    return User.objects.create_user(phone="09120000001", password="Str0ngPass!9")


@pytest.fixture
def other_owner(db):
    return User.objects.create_user(phone="09120000002", password="Str0ngPass!9")


@pytest.fixture
def category(db):
    return AnimalCategory.objects.get(slug="companion-pets")


@pytest.mark.django_db
def test_animals_list_requires_login():
    resp = Client().get(reverse("animals:list"))
    assert resp.status_code == 302
    assert reverse("accounts:login") in resp.url


@pytest.mark.django_db
def test_owner_can_create_animal(owner, category):
    client = Client()
    client.force_login(owner)
    resp = client.post(
        reverse("animals:create"),
        {"name": "پیشی", "animal_category": category.pk, "species": "گربه",
         "sex": "female"},
    )
    assert resp.status_code == 302
    animal = Animal.objects.get(name="پیشی")
    assert animal.owner == owner


@pytest.mark.django_db
def test_owner_cannot_access_others_animal(owner, other_owner, category):
    animal = Animal.objects.create(
        owner=other_owner, animal_category=category, name="غریبه", species="سگ"
    )
    client = Client()
    client.force_login(owner)
    assert client.get(reverse("animals:detail", args=[animal.pk])).status_code == 404
    assert client.get(reverse("animals:update", args=[animal.pk])).status_code == 404


@pytest.mark.django_db
def test_admin_animal_autocomplete_shows_owner_and_category(owner, category):
    from core.admin_site import VetAutocompleteJsonView

    owner.full_name = "علی رضایی"
    owner.save()
    animal = Animal.objects.create(
        owner=owner, animal_category=category, name="رکس", species="سگ"
    )

    result = VetAutocompleteJsonView().serialize_result(animal, "pk")
    assert "رکس" in result["text"]
    assert "علی رضایی" in result["text"]      # owner shown for disambiguation
    assert owner.phone in result["text"]
    assert result["category_id"] == category.pk  # drives the prescription filter


@pytest.mark.django_db
def test_owner_can_create_herd(owner, db):
    ruminants = AnimalCategory.objects.get(slug="ruminants")
    client = Client()
    client.force_login(owner)
    resp = client.post(
        reverse("animals:herd_create"),
        {"name": "گلهٔ شمالی", "animal_category": ruminants.pk,
         "species": "گوسفند", "head_count": 200, "farm_location": "اردبیل"},
    )
    assert resp.status_code == 302
    herd = Herd.objects.get(name="گلهٔ شمالی")
    assert herd.owner == owner
    assert herd.head_count == 200
