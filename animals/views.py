"""Owner-facing CRUD for Animals and Herds.

All views are login-required and scoped to the requesting Owner: querysets are
filtered by ``owner=request.user`` so one Owner can never see or edit another's
records.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import AnimalForm, HerdForm
from .models import Animal, Herd


class OwnerScopedMixin(LoginRequiredMixin):
    """Restrict the queryset to objects owned by the current user."""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class OwnerCreateMixin(LoginRequiredMixin):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


# --- Combined dashboard ----------------------------------------------------
class MyAnimalsView(LoginRequiredMixin, ListView):
    template_name = "animals/my_animals.html"
    context_object_name = "animals"

    def get_queryset(self):
        return Animal.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["herds"] = Herd.objects.filter(owner=self.request.user)
        return ctx


# --- Animal CRUD -----------------------------------------------------------
class AnimalDetailView(OwnerScopedMixin, DetailView):
    model = Animal
    template_name = "animals/animal_detail.html"


class AnimalCreateView(OwnerCreateMixin, CreateView):
    model = Animal
    form_class = AnimalForm
    template_name = "animals/animal_form.html"


class AnimalUpdateView(OwnerScopedMixin, UpdateView):
    model = Animal
    form_class = AnimalForm
    template_name = "animals/animal_form.html"


class AnimalDeleteView(OwnerScopedMixin, DeleteView):
    model = Animal
    template_name = "animals/confirm_delete.html"
    success_url = reverse_lazy("animals:list")


# --- Herd CRUD -------------------------------------------------------------
class HerdDetailView(OwnerScopedMixin, DetailView):
    model = Herd
    template_name = "animals/herd_detail.html"


class HerdCreateView(OwnerCreateMixin, CreateView):
    model = Herd
    form_class = HerdForm
    template_name = "animals/herd_form.html"


class HerdUpdateView(OwnerScopedMixin, UpdateView):
    model = Herd
    form_class = HerdForm
    template_name = "animals/herd_form.html"


class HerdDeleteView(OwnerScopedMixin, DeleteView):
    model = Herd
    template_name = "animals/confirm_delete.html"
    success_url = reverse_lazy("animals:list")
