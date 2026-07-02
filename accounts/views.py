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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from notifications.backends.base import SMSDeliveryError
from notifications.service import notify

from .forms import (
    OTPVerifyForm,
    OwnerProfileForm,
    PasswordResetRequestForm,
    PhoneAuthenticationForm,
    ProfileForm,
    RegistrationForm,
    SetNewPasswordForm,
)
from .models import OwnerProfile, User
from .otp import send_otp, verify_otp

# Session keys for the pending (not-yet-verified) registration / reset.
REG_SESSION_KEY = "pending_registration"
RESET_SESSION_KEY = "pending_reset_phone"
AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        from .captcha import new_question

        ctx = super().get_context_data(**kwargs)
        ctx["captcha_question"] = new_question(self.request.session)
        return ctx


class LogoutView(auth_views.LogoutView):
    pass


class ProfileView(LoginRequiredMixin, View):
    """The owner views and edits their own account: name, email, address, and
    notification preferences. Phone is the login identity and is shown read-only."""

    template_name = "accounts/profile.html"

    def _context(self, request, form=None, profile_form=None):
        profile, _ = OwnerProfile.objects.get_or_create(user=request.user)
        return {
            "form": form or ProfileForm(instance=request.user),
            "profile_form": profile_form or OwnerProfileForm(instance=profile),
        }

    def get(self, request):
        return render(request, self.template_name, self._context(request))

    def post(self, request):
        profile, _ = OwnerProfile.objects.get_or_create(user=request.user)
        form = ProfileForm(request.POST, instance=request.user)
        profile_form = OwnerProfileForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, "اطلاعات حساب شما به‌روزرسانی شد.")
            return redirect("accounts:profile")
        return render(
            request, self.template_name, self._context(request, form, profile_form)
        )


class RegisterView(View):
    template_name = "registration/register.html"

    def _render(self, request, form):
        from .captcha import new_question

        return render(
            request,
            self.template_name,
            {"form": form, "captcha_question": new_question(request.session)},
        )

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("pages:home")
        return self._render(request, RegistrationForm(request=request))

    def post(self, request):
        form = RegistrationForm(request.POST, request=request)
        if not form.is_valid():
            return self._render(request, form)

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
            return self._render(request, form)
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
        messages.success(
            request,
            "حساب شما ساخته شد. لطفاً برای تکمیل پروفایل، نشانی و کد پستی خود را "
            "وارد کنید تا امکان ارسال سفارش‌ها فراهم شود.",
        )
        # Send new owners to complete their profile (address + postal code) so
        # delivery details exist before they order.
        return redirect("accounts:profile")


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
