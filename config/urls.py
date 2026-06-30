"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("animals/", include("animals.urls")),
    path("shop/", include("pharmacy.urls")),
    path("clinic/", include("appointments.urls")),
    path("payments/", include("payments.urls")),
    path("c/", include("catalog.urls")),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
