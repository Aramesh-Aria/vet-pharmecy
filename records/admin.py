from django.contrib import admin

from core.admin_mixins import JalaliAdminMixin

from .models import Vaccination, VisitRecord


@admin.register(VisitRecord)
class VisitRecordAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("animal", "date", "service", "vet")
    list_filter = ("date",)
    search_fields = ("animal__name", "animal__owner__phone", "notes")
    autocomplete_fields = ("animal", "appointment", "service", "vet")
    date_hierarchy = "date"


@admin.register(Vaccination)
class VaccinationAdmin(JalaliAdminMixin, admin.ModelAdmin):
    list_display = ("animal", "vaccine_name", "date_given", "next_due", "reminded_at")
    list_filter = ("vaccine_name", "next_due")
    search_fields = ("animal__name", "animal__owner__phone", "vaccine_name")
    autocomplete_fields = ("animal",)
    # reminded_at is managed by the reminder job, not entered by staff.
    readonly_fields = ("reminded_at",)
    date_hierarchy = "next_due"
