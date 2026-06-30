from django import forms

from animals.models import Animal
from catalog.models import Service


class AppointmentRequestForm(forms.Form):
    """Owner picks one of their Animals, a Service, and a preferred date."""

    animal = forms.ModelChoiceField(
        queryset=Animal.objects.none(), label="حیوان"
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True), label="خدمت"
    )
    preferred_date = forms.DateField(
        label="تاریخ پیشنهادی", widget=forms.DateInput(attrs={"type": "date"})
    )
    preferred_time_note = forms.CharField(
        label="بازهٔ زمانی پیشنهادی", required=False, max_length=100
    )
    owner_note = forms.CharField(
        label="توضیحات", required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields["animal"].queryset = Animal.objects.filter(owner=owner)
