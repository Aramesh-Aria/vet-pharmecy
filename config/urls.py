"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from pages.sitemaps import SITEMAPS
from pages.views import healthz, robots_txt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("animals/", include("animals.urls")),
    path("shop/", include("pharmacy.urls")),
    path("clinic/", include("appointments.urls")),
    path("payments/", include("payments.urls")),
    path("c/", include("catalog.urls")),
    # SEO + ops
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    path("healthz", healthz, name="healthz"),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
