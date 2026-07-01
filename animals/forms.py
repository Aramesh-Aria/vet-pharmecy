from django import forms

from catalog.models import AnimalCategory
from core.widgets import JalaliDateInput, PrettyImageInput

from .models import Animal, Herd


def _active_categories():
    return AnimalCategory.objects.filter(is_active=True)


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = [
            "name", "animal_category", "species", "sex",
            "birth_date", "weight_kg", "photo",
        ]
        widgets = {"birth_date": JalaliDateInput(), "photo": PrettyImageInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["animal_category"].queryset = _active_categories()


class HerdForm(forms.ModelForm):
    class Meta:
        model = Herd
        fields = [
            "name", "animal_category", "species", "head_count", "farm_location",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["animal_category"].queryset = _active_categories()
