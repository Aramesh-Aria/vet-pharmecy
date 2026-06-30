"""Tests for upload image processing (core.images)."""
import shutil
import tempfile
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from animals.models import Animal
from catalog.models import AnimalCategory

_MEDIA = tempfile.mkdtemp()


def _upload(name, size, color=(10, 120, 200), fmt="PNG"):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt)
    content = buf.getvalue()
    return SimpleUploadedFile(name, content, content_type=f"image/{fmt.lower()}"), len(content)


@pytest.fixture(autouse=True)
def _temp_media():
    with override_settings(MEDIA_ROOT=_MEDIA):
        yield
    shutil.rmtree(_MEDIA, ignore_errors=True)


@pytest.mark.django_db
def test_category_tile_cropped_to_square():
    upload, _ = _upload("tile.png", (1600, 900))
    cat = AnimalCategory.objects.create(name="تست", slug="test-cat", image=upload)

    with Image.open(cat.image.path) as img:
        assert img.size == (600, 600)  # fit -> exact square
    assert cat.image.name.endswith(".jpg")  # normalised to JPEG


@pytest.mark.django_db
def test_animal_photo_shrunk_within_bounds_and_smaller():
    # A big, highly-compressible PNG; JPEG re-encode should shrink the bytes.
    upload, original_bytes = _upload("pet.png", (3000, 2000))
    owner_cat = AnimalCategory.objects.get(slug="companion-pets")
    from accounts.models import User

    owner = User.objects.create_user(phone="09120000009", password="Str0ngPass!9")
    animal = Animal.objects.create(
        owner=owner, animal_category=owner_cat, name="عکسی", species="گربه", photo=upload
    )

    with Image.open(animal.photo.path) as img:
        assert max(img.size) <= 1200  # shrunk within bounds
        assert img.size[0] / img.size[1] == pytest.approx(3000 / 2000, abs=0.01)
    assert animal.photo.size < original_bytes  # compressed


@pytest.mark.django_db
def test_resaving_without_new_image_keeps_file():
    upload, _ = _upload("tile.png", (800, 800))
    cat = AnimalCategory.objects.create(name="ثابت", slug="stable", image=upload)
    first_name = cat.image.name

    cat.name = "ثابت ۲"
    cat.save()
    assert cat.image.name == first_name  # not re-processed into a new file
