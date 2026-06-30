from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("<slug:slug>/", views.CategoryLandingView.as_view(), name="category"),
    path(
        "<slug:slug>/<str:section>/",
        views.SectionView.as_view(),
        name="section",
    ),
    path(
        "<slug:slug>/<str:section>/<slug:product_slug>/",
        views.ProductDetailView.as_view(),
        name="product",
    ),
]
