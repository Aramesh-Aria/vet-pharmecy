"""Auth forms keyed on phone (ADR-0004)."""
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from . import captcha
from .models import OwnerProfile, User
from .validators import normalize_phone, normalize_postal_code


def _captcha_field():
    return forms.CharField(
        label="کد امنیتی",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
    )


class CaptchaValidationMixin:
    """Validate the ``captcha`` field against the challenge in the session.
    The form must be given the request (``self.request``)."""

    def clean_captcha(self):
        value = self.cleaned_data.get("captcha", "")
        session = getattr(getattr(self, "request", None), "session", None)
        if session is None or not captcha.check(session, value):
            raise forms.ValidationError("پاسخ کد امنیتی نادرست است.")
        return value


class ProfileForm(forms.ModelForm):
    """The owner edits their own contact name + email."""

    class Meta:
        model = User
        fields = ("full_name", "email")


class OwnerProfileForm(forms.ModelForm):
    """The owner edits their address, postal code + notification preferences."""

    class Meta:
        model = OwnerProfile
        fields = (
            "province", "city", "address", "postal_code",
            "notify_by_sms", "notify_by_email",
        )
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "postal_code": forms.TextInput(attrs={"inputmode": "numeric"}),
        }

    def clean_postal_code(self):
        value = self.cleaned_data.get("postal_code", "")
        return normalize_postal_code(value) if value else value


class PhoneAuthenticationForm(CaptchaValidationMixin, AuthenticationForm):
    """Login with phone + password. The username field IS the phone."""

    username = forms.CharField(
        label="شماره موبایل",
        widget=forms.TextInput(attrs={"autofocus": True, "inputmode": "tel"}),
    )
    captcha = _captcha_field()

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


class _PhoneField(forms.CharField):
    def clean(self, value):
        return normalize_phone(super().clean(value))


class _PasswordPairMixin:
    """Validate that two password fields match and pass Django's validators."""

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("گذرواژه‌ها یکسان نیستند.")
        password_validation.validate_password(p2)
        return p2


class RegistrationForm(CaptchaValidationMixin, _PasswordPairMixin, forms.Form):
    """Collect registration details. The account is created only after the
    phone is verified by OTP (see the register/verify views)."""

    phone = _PhoneField(
        label="شماره موبایل", max_length=15,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autofocus": True}),
    )
    full_name = forms.CharField(label="نام و نام خانوادگی", max_length=150)
    password1 = forms.CharField(
        label="گذرواژه",
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(label="تکرار گذرواژه", widget=forms.PasswordInput)
    captcha = _captcha_field()

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("این شماره قبلاً ثبت شده است.")
        return phone


def _ascii_code(value: str) -> str:
    """Strip spaces and convert Persian/Arabic digits to ASCII."""
    digit_map = {ord(p): str(i) for i, p in enumerate("۰۱۲۳۴۵۶۷۸۹")}
    digit_map.update({ord(a): str(i) for i, a in enumerate("٠١٢٣٤٥٦٧٨٩")})
    return value.strip().translate(digit_map)


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="کد تأیید",
        max_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autofocus": True}),
    )

    def clean_code(self):
        return _ascii_code(self.cleaned_data["code"])


class PasswordResetRequestForm(forms.Form):
    phone = _PhoneField(label="شماره موبایل", max_length=15)


class SetNewPasswordForm(_PasswordPairMixin, forms.Form):
    code = forms.CharField(
        label="کد تأیید",
        max_length=6,
        widget=forms.TextInput(attrs={"inputmode": "numeric"}),
    )
    password1 = forms.CharField(label="گذرواژهٔ جدید", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار گذرواژهٔ جدید", widget=forms.PasswordInput)

    def clean_code(self):
        return _ascii_code(self.cleaned_data["code"])
