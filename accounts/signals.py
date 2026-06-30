"""Ensure every Owner account has a profile."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OwnerProfile, User


@receiver(post_save, sender=User)
def ensure_owner_profile(sender, instance, created, **kwargs):
    if instance.is_owner:
        OwnerProfile.objects.get_or_create(user=instance)
