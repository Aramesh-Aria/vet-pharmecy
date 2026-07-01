from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # Must precede the <slug> patterns so "products" isn't read as a category slug.
    path("products/", views.AllProductsView.as_view(), name="products"),
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
