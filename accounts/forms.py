"""Auth forms keyed on phone (ADR-0004)."""
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User
from .validators import normalize_phone


class PhoneAuthenticationForm(AuthenticationForm):
    """Login with phone + password. The username field IS the phone."""

    username = forms.CharField(
        label="شماره موبایل",
        widget=forms.TextInput(attrs={"autofocus": True, "inputmode": "tel"}),
    )

    def clean_username(self):
        return normalize_phone(self.cleaned_data["username"])


class UserAdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("phone", "full_name", "email", "role")


class UserAdminChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"
