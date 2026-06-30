"""Image processing for uploads (resize + compress).

Uploaded images vary wildly in size and dimensions; we normalise them so the
site looks consistent and pages stay light. Two strategies:

- ``fit=(w, h)``      — crop to exactly w×h (uniform tiles, e.g. category images).
- ``max_size=(w, h)`` — shrink to fit within w×h, keeping aspect ratio, never
  upscaling (general photos).

Output is JPEG (good compression, universal support). Use the
:class:`ImageProcessingMixin` on a model to process declared image fields on
save; both portal forms and the Django admin go through ``Model.save`` so both
are covered.
"""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

DEFAULT_QUALITY = 82


def compress_image(
    fieldfile,
    *,
    fit=None,
    max_size=None,
    quality=DEFAULT_QUALITY,
) -> ContentFile | None:
    """Return a processed :class:`ContentFile` for *fieldfile*, or None on
    failure. Honours EXIF orientation and flattens transparency onto white."""
    try:
        fieldfile.open()
        img = Image.open(fieldfile)
        img = ImageOps.exif_transpose(img)  # respect camera rotation

        # Flatten alpha / palette onto a white background for JPEG.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            background = Image.new("RGBA", img.size, (255, 255, 255, 255))
            img = Image.alpha_composite(background, img).convert("RGB")
        else:
            img = img.convert("RGB")

        if fit:
            img = ImageOps.fit(img, fit, method=Image.LANCZOS)
        elif max_size:
            img.thumbnail(max_size, Image.LANCZOS)  # in-place, shrink-only

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
    except (OSError, ValueError):
        return None

    stem = os.path.splitext(os.path.basename(fieldfile.name or "image"))[0]
    return ContentFile(buffer.getvalue(), name=f"{stem}.jpg")


class ImageProcessingMixin(models.Model):
    """Abstract mixin: declare ``image_specs`` and freshly-uploaded images on
    those fields are resized/compressed on save.

    Example::

        image_specs = {"photo": {"max_size": (1200, 1200)}}
    """

    image_specs: dict[str, dict] = {}

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for name, spec in self.image_specs.items():
            field = getattr(self, name)
            # ``_committed`` is False only for a freshly-assigned upload not yet
            # written to storage. So we process new uploads (on create or
            # update) and skip files already stored — re-saving an unchanged
            # record never re-compresses.
            if field and not getattr(field, "_committed", True):
                processed = compress_image(field, **spec)
                if processed is not None:
                    field.save(processed.name, processed, save=False)
        super().save(*args, **kwargs)
