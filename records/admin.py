from django.contrib import admin

from .models import Vaccination, VisitRecord


@admin.register(VisitRecord)
class VisitRecordAdmin(admin.ModelAdmin):
    list_display = ("animal", "date", "service", "vet")
    list_filter = ("date",)
    search_fields = ("animal__name", "animal__owner__phone", "notes")
    autocomplete_fields = ("animal", "appointment", "service", "vet")
    date_hierarchy = "date"


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("animal", "vaccine_name", "date_given", "next_due", "reminded_at")
    list_filter = ("vaccine_name", "next_due")
    search_fields = ("animal__name", "animal__owner__phone", "vaccine_name")
    autocomplete_fields = ("animal",)
    date_hierarchy = "next_due"
