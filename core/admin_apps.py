"""Admin app config that swaps in our dashboard-equipped admin site.

Kept in its own module (not core/apps.py) so importing AdminConfig doesn't
collide with CoreConfig during app-config discovery.
"""
from django.contrib.admin.apps import AdminConfig


class VetAdminConfig(AdminConfig):
    default_site = "core.admin_site.VetAdminSite"
