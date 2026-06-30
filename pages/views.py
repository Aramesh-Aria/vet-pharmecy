from django.views.generic import TemplateView

from catalog.models import AnimalCategory


class HomeView(TemplateView):
    """Public home page: one tile per active Animal Category (ADR-0006)."""

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = AnimalCategory.objects.filter(is_active=True)
        return ctx
