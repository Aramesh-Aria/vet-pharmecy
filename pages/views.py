from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Public home page. Category tiles are added in Phase 1 (ADR-0006)."""

    template_name = "pages/home.html"
