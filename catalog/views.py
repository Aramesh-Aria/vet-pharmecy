"""Category landing, section listing, and product detail pages (ADR-0006).

URL scheme:
- ``/c/<slug>/``                       — category landing (the four Sections)
- ``/c/<slug>/<section>/``             — a Section; Medication/Equipment list
                                         Products (with filters); Service and
                                         Online Visit are placeholders (Phases 3, 5)
- ``/c/<slug>/<section>/<product>/``   — Product detail
"""
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import AnimalCategory, Product, Section, Service

PRODUCTS_PER_PAGE = 12


def paginate_products(request, queryset):
    """Slice a product queryset into pages and return the template context bits
    (the current page + an elided page range + a `page`-free querystring for links)."""
    paginator = Paginator(queryset, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return {
        "products": page_obj,
        "page_obj": page_obj,
        "total_count": paginator.count,
        "page_range": paginator.get_elided_page_range(
            page_obj.number, on_each_side=1, on_ends=1
        ),
        "base_qs": params.urlencode(),
    }


class AllProductsView(TemplateView):
    """Global shop: every Medication/Equipment Product across all categories,
    with faceted filters (animal category, section, prescription flag, search,
    in-stock). HTMX swaps just the results grid."""

    template_name = "catalog/all_products.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        get = self.request.GET

        product_sections = [s.value for s in Section.product_sections()]
        products = Product.objects.filter(
            is_active=True, section__in=product_sections
        ).select_related("animal_category")

        selected_cats = get.getlist("category")
        if selected_cats:
            products = products.filter(animal_category__slug__in=selected_cats)

        selected_secs = [s for s in get.getlist("section") if s in product_sections]
        if selected_secs:
            products = products.filter(section__in=selected_secs)

        selected_rx = [r for r in get.getlist("rx") if r in ("yes", "no")]
        if selected_rx == ["yes"]:
            products = products.filter(is_prescription_only=True)
        elif selected_rx == ["no"]:
            products = products.filter(is_prescription_only=False)

        q = get.get("q", "").strip()
        if q:
            products = products.filter(name__icontains=q)
        if get.get("in_stock"):
            products = products.filter(stock__gt=0)

        products = products.order_by("animal_category__order", "name")
        ctx.update(paginate_products(self.request, products))
        ctx["q"] = q
        ctx["categories"] = AnimalCategory.objects.filter(is_active=True)
        ctx["sections"] = [(s.value, s.label) for s in Section.product_sections()]
        ctx["selected_cats"] = selected_cats
        ctx["selected_secs"] = selected_secs
        ctx["selected_rx"] = selected_rx
        ctx["has_filters"] = bool(
            selected_cats or selected_secs or selected_rx or q or get.get("in_stock")
        )
        return ctx


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
            ctx.update(paginate_products(self.request, products.order_by("name")))
            ctx["q"] = q
        elif section == Section.SERVICE:
            ctx["services"] = Service.objects.filter(
                animal_category=category, is_active=True
            )
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
