"""Owner-facing appointment views. Login-required and owner-scoped."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from . import services
from .forms import AppointmentRequestForm
from .models import Appointment


@login_required
def request_appointment(request):
    initial = {}
    if request.method == "GET" and request.GET.get("service"):
        initial["service"] = request.GET.get("service")

    if request.method == "POST":
        form = AppointmentRequestForm(request.POST, owner=request.user)
        if form.is_valid():
            try:
                appointment = services.request_appointment(
                    request.user,
                    animal=form.cleaned_data["animal"],
                    service=form.cleaned_data["service"],
                    preferred_date=form.cleaned_data["preferred_date"],
                    preferred_time_note=form.cleaned_data["preferred_time_note"],
                    owner_note=form.cleaned_data["owner_note"],
                )
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
            else:
                messages.success(request, "درخواست نوبت ثبت شد. پس از تأیید اطلاع‌رسانی می‌شود.")
                return redirect(appointment.get_absolute_url())
    else:
        form = AppointmentRequestForm(owner=request.user, initial=initial)

    return render(request, "appointments/request.html", {"form": form})


class AppointmentListView(LoginRequiredMixin, ListView):
    template_name = "appointments/list.html"
    context_object_name = "appointments"

    def get_queryset(self):
        return Appointment.objects.filter(owner=self.request.user).select_related(
            "animal", "service"
        )


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    template_name = "appointments/detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return Appointment.objects.filter(owner=self.request.user)


@login_required
@require_POST
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, owner=request.user)
    try:
        services.cancel_by_owner(appointment, request.user)
        messages.success(request, "نوبت لغو شد.")
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("appointments:detail", pk=pk)
