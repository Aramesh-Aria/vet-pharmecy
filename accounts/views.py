"""Auth views: phone+password login, OTP registration, and OTP password reset
(ADR-0004).

Registration creates no account until the phone is OTP-verified: the submitted
details (with an already-hashed password) are parked in the session and the
User row is created only on successful verification, so unverified phones never
litter the table.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from notifications.backends.base import SMSDeliveryError
from notifications.service import notify

from .forms import (
    OTPVerifyForm,
    PasswordResetRequestForm,
    PhoneAuthenticationForm,
    RegistrationForm,
    SetNewPasswordForm,
)
from .models import User
from .otp import send_otp, verify_otp

# Session keys for the pending (not-yet-verified) registration / reset.
REG_SESSION_KEY = "pending_registration"
RESET_SESSION_KEY = "pending_reset_phone"
AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class RegisterView(View):
    template_name = "registration/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("pages:home")
        return render(request, self.template_name, {"form": RegistrationForm()})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        phone = form.cleaned_data["phone"]
        request.session[REG_SESSION_KEY] = {
            "phone": phone,
            "full_name": form.cleaned_data["full_name"],
            "password": make_password(form.cleaned_data["password1"]),
        }
        try:
            send_otp(phone, "register")
        except SMSDeliveryError:
            messages.error(request, "ارسال پیامک ناموفق بود. لطفاً دوباره تلاش کنید.")
            return render(request, self.template_name, {"form": form})
        return redirect("accounts:register_verify")


class RegisterVerifyView(View):
    template_name = "registration/verify.html"

    def dispatch(self, request, *args, **kwargs):
        self.pending = request.session.get(REG_SESSION_KEY)
        if not self.pending:
            return redirect("accounts:register")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": OTPVerifyForm(), "phone": self.pending["phone"]},
        )

    def post(self, request):
        form = OTPVerifyForm(request.POST)
        ctx = {"form": form, "phone": self.pending["phone"]}
        if not form.is_valid():
            return render(request, self.template_name, ctx)

        if not verify_otp(self.pending["phone"], "register", form.cleaned_data["code"]):
            messages.error(request, "کد نادرست یا منقضی شده است.")
            return render(request, self.template_name, ctx)

        user = User(
            phone=self.pending["phone"],
            full_name=self.pending["full_name"],
            role=User.Role.OWNER,
            phone_verified=True,
        )
        user.password = self.pending["password"]  # already hashed
        user.save()
        del request.session[REG_SESSION_KEY]

        login(request, user, backend=AUTH_BACKEND)
        try:
            notify(user, "welcome")
        except Exception:
            pass  # welcome message is best-effort
        messages.success(request, "حساب شما با موفقیت ساخته شد.")
        return redirect("pages:home")


class ResendRegisterOTPView(View):
    def post(self, request):
        pending = request.session.get(REG_SESSION_KEY)
        if not pending:
            return redirect("accounts:register")
        try:
            send_otp(pending["phone"], "register")
            messages.success(request, "کد جدید ارسال شد.")
        except SMSDeliveryError:
            messages.error(request, "ارسال پیامک ناموفق بود.")
        return redirect("accounts:register_verify")


class PasswordResetRequestView(View):
    template_name = "registration/reset_request.html"

    def get(self, request):
        return render(request, self.template_name, {"form": PasswordResetRequestForm()})

    def post(self, request):
        form = PasswordResetRequestForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        phone = form.cleaned_data["phone"]
        request.session[RESET_SESSION_KEY] = phone
        # Avoid leaking which phones are registered: only send if a user exists,
        # but always advance to the confirm step with the same message.
        if User.objects.filter(phone=phone).exists():
            try:
                send_otp(phone, "reset")
            except SMSDeliveryError:
                messages.error(request, "ارسال پیامک ناموفق بود. دوباره تلاش کنید.")
                return render(request, self.template_name, {"form": form})
        return redirect("accounts:reset_confirm")


class PasswordResetConfirmView(View):
    template_name = "registration/reset_confirm.html"

    def dispatch(self, request, *args, **kwargs):
        self.phone = request.session.get(RESET_SESSION_KEY)
        if not self.phone:
            return redirect("accounts:reset")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(
            request, self.template_name, {"form": SetNewPasswordForm(), "phone": self.phone}
        )

    def post(self, request):
        form = SetNewPasswordForm(request.POST)
        ctx = {"form": form, "phone": self.phone}
        if not form.is_valid():
            return render(request, self.template_name, ctx)

        if not verify_otp(self.phone, "reset", form.cleaned_data["code"]):
            messages.error(request, "کد نادرست یا منقضی شده است.")
            return render(request, self.template_name, ctx)

        user = User.objects.filter(phone=self.phone).first()
        if user is None:
            messages.error(request, "کاربری با این شماره یافت نشد.")
            return redirect("accounts:reset")
        user.set_password(form.cleaned_data["password1"])
        if not user.phone_verified:
            user.phone_verified = True  # proven ownership of the number
        user.save()
        del request.session[RESET_SESSION_KEY]
        messages.success(request, "گذرواژه با موفقیت تغییر کرد. اکنون وارد شوید.")
        return redirect(reverse("accounts:login"))
