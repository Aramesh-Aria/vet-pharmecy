from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Registration with phone OTP verification.
    path("register/", views.RegisterView.as_view(), name="register"),
    path("register/verify/", views.RegisterVerifyView.as_view(), name="register_verify"),
    path("register/resend/", views.ResendRegisterOTPView.as_view(), name="register_resend"),
    # Password reset via phone OTP.
    path("reset/", views.PasswordResetRequestView.as_view(), name="reset"),
    path("reset/confirm/", views.PasswordResetConfirmView.as_view(), name="reset_confirm"),
]
