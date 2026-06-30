"""Auth views.

Phase 0 ships phone+password login/logout. Phone-OTP registration and password
reset (ADR-0004) arrive in Phase 1.
"""
from django.contrib.auth import views as auth_views

from .forms import PhoneAuthenticationForm


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass
