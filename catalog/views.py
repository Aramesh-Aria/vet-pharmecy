"""Category landing, section listing, and product detail pages (ADR-0006).

URL scheme:
- ``/c/<slug>/``                       — category landing (the four Sections)
- ``/c/<slug>/<section>/``             — a Section; Medication/Equipment list
                                         Products (with filters); Service and
                                         Online Visit are placeholders (Phases 3, 5)
- ``/c/<slug>/<section>/<product>/``   — Product detail
"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import AnimalCategory, Product, Section


class CategoryLandingView(TemplateView):
    template_name = "catalog/category_landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = get_object_or_404(
            AnimalCategory, slug=kwargs["slug"], is_active=True
        )
        ctx["sections"] = Section.choices
        return ctx


class SectionView(TemplateView):
    template_name = "catalog/section.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        section = kwargs["section"]
        if section not in Section.values:
            raise Http404("بخش نامعتبر است.")
        category = get_object_or_404(
            AnimalCategory, slug=kwargs["slug"], is_active=True
        )
        ctx["category"] = category
        ctx["section"] = section
        ctx["section_label"] = Section(section).label
        ctx["is_product_section"] = section in Section.values and section in [
            s.value for s in Section.product_sections()
        ]

        if ctx["is_product_section"]:
            products = Product.objects.filter(
                animal_category=category, section=section, is_active=True
            )
            # Filters: free-text search, in-stock only, price range.
            q = self.request.GET.get("q", "").strip()
            if q:
                products = products.filter(name__icontains=q)
            if self.request.GET.get("in_stock"):
                products = products.filter(stock__gt=0)
            ctx["products"] = products
            ctx["q"] = q
        return ctx


class ProductDetailView(TemplateView):
    template_name = "catalog/product_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = get_object_or_404(
            Product.objects.select_related("animal_category"),
            slug=kwargs["product_slug"],
            animal_category__slug=kwargs["slug"],
            section=kwargs["section"],
            is_active=True,
        )
        ctx["product"] = product
        ctx["category"] = product.animal_category
        return ctx
