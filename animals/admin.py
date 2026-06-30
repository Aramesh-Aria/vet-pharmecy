from django.contrib import admin

from .models import Animal, Herd


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "animal_category", "owner", "sex")
    list_filter = ("animal_category", "sex")
    search_fields = ("name", "species", "owner__phone", "owner__full_name")
    autocomplete_fields = ("owner",)


@admin.register(Herd)
class HerdAdmin(admin.ModelAdmin):
    list_display = ("__str__", "species", "head_count", "animal_category", "owner")
    list_filter = ("animal_category",)
    search_fields = ("name", "species", "owner__phone", "owner__full_name")
    autocomplete_fields = ("owner",)
