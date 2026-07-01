from django.contrib import admin

from core.admin_mixins import JalaliAdminMixin

from . import services
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = (
        "id", "owner", "animal", "service", "status",
        "preferred_date", "confirmed_datetime", "vet",
    )
    list_filter = ("status", "is_online", "preferred_date")
    search_fields = ("owner__phone", "owner__full_name", "animal__name", "id")
    autocomplete_fields = ("owner", "animal", "service", "vet")
    actions = ("confirm", "complete", "cancel", "mark_no_show")

    @admin.action(description="تأیید نوبت‌ها (نیازمند زمان تأییدشده)")
    def confirm(self, request, queryset):
        done = 0
        for appt in queryset:
            if appt.confirmed_datetime:
                services.set_appointment_status(appt, Appointment.Status.CONFIRMED)
                done += 1
        self.message_user(
            request,
            f"{done} نوبت تأیید شد. (نوبت‌های بدون «زمان تأییدشده» نادیده گرفته شدند.)",
        )

    @admin.action(description="ثبت انجام‌شده")
    def complete(self, request, queryset):
        for appt in queryset:
            services.set_appointment_status(appt, Appointment.Status.COMPLETED)
        self.message_user(request, f"{queryset.count()} نوبت انجام‌شده ثبت شد.")

    @admin.action(description="لغو نوبت‌ها")
    def cancel(self, request, queryset):
        for appt in queryset:
            services.set_appointment_status(appt, Appointment.Status.CANCELLED)
        self.message_user(request, f"{queryset.count()} نوبت لغو شد.")

    @admin.action(description="ثبت عدم مراجعه")
    def mark_no_show(self, request, queryset):
        for appt in queryset:
            services.set_appointment_status(appt, Appointment.Status.NO_SHOW)
        self.message_user(request, f"{queryset.count()} نوبت «عدم مراجعه» ثبت شد.")
