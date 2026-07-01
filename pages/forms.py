from django import forms

from accounts.validators import normalize_phone

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "phone", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}

    def clean_phone(self):
        return normalize_phone(self.cleaned_data["phone"])
