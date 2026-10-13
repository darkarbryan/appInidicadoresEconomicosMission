"""URL routes for authentication endpoints."""

from django.urls import path

from apps.users.views import (
    AuthTokenRefreshView,
    LoginView,
    LogoutView,
    MeView,
    PasswordRecoveryView,
    PasswordResetView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", AuthTokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("password-recovery/", PasswordRecoveryView.as_view(), name="auth-password-recovery"),
    path("password-reset/", PasswordResetView.as_view(), name="auth-password-reset"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
]
