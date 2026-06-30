from django.contrib import admin

from .models import AnimalCategory, Product


@admin.register(AnimalCategory)
class AnimalCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "animal_category", "section", "price", "stock",
        "is_prescription_only", "is_active",
    )
    list_filter = ("animal_category", "section", "is_prescription_only", "is_active")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
