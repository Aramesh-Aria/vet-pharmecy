"""Sitemaps for local-business SEO (ADR-0001 notes SEO matters)."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import AnimalCategory, Product


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return ["pages:home", "pages:contact", "pages:about", "pages:terms",
                "catalog:products"]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return AnimalCategory.objects.filter(is_active=True)


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Product.objects.filter(is_active=True).select_related("animal_category")


SITEMAPS = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}
