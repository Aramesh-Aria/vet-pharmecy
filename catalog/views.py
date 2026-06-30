"""Category landing and section pages (ADR-0006).

URL scheme: ``/c/<slug>/`` for a category's landing page (the four Sections)
and ``/c/<slug>/<section>/`` for a single Section. Product/Service contents of
the sections arrive in Phases 2-3; for now the section pages are placeholders.
"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from .models import AnimalCategory, Section


class CategoryLandingView(TemplateView):
    template_name = "catalog/category_landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = get_object_or_404(
            AnimalCategory, slug=kwargs["slug"], is_active=True
        )
        ctx["sections"] = Section.choices  # [(value, label), ...]
        return ctx


class SectionView(TemplateView):
    template_name = "catalog/section.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        section = kwargs["section"]
        if section not in Section.values:
            raise Http404("بخش نامعتبر است.")
        ctx["category"] = get_object_or_404(
            AnimalCategory, slug=kwargs["slug"], is_active=True
        )
        ctx["section"] = section
        ctx["section_label"] = Section(section).label
        return ctx
