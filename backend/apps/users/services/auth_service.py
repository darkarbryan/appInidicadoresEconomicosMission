"""Authentication and password-recovery business operations."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Rol, User

password_reset_token_generator = PasswordResetTokenGenerator()

GENERIC_RECOVERY_MESSAGE = (
    "Si el correo está registrado, recibirás instrucciones para restablecer tu contraseña."
)
PASSWORD_RESET_SUCCESS_MESSAGE = "La contraseña se actualizó correctamente."


def issue_tokens_for_user(user: User) -> dict:
    """Generate access and refresh JWT tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def register_user(*, email: str, password: str, nombre_completo: str) -> tuple[User, dict]:
    """
    Register a new analyst user and return the user with JWT tokens.

    Raises IntegrityError if email already exists (handled by serializer validation).
    """
    user = User.objects.create_user(
        email=email,
        password=password,
        nombre_completo=nombre_completo,
        rol=Rol.ANALISTA,
        activo=True,
    )
    tokens = issue_tokens_for_user(user)
    return user, tokens


def authenticate_user(*, email: str, password: str) -> tuple[User | None, str | None]:
    """
    Validate credentials and return the user when authentication succeeds.

    Returns (user, None) on success or (None, error_message) on failure.
    """
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return None, "Credenciales inválidas."

    if not user.activo:
        return None, "La cuenta está desactivada."

    if not user.check_password(password):
        return None, "Credenciales inválidas."

    return user, None


def logout_user(*, refresh_token: str) -> str | None:
    """
    Blacklist the provided refresh token to close the JWT session.

    Returns an error message when the token is invalid; otherwise None.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        return "El token de actualización no es válido o ya fue invalidado."
    return None


def request_password_recovery(*, email: str) -> str:
    """
    Send a password-recovery email when the account exists and is active.

    Always returns the same generic message to avoid email enumeration.
    """
    try:
        user = User.objects.get(email__iexact=email, activo=True)
    except User.DoesNotExist:
        return GENERIC_RECOVERY_MESSAGE

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token_generator.make_token(user)
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200").rstrip("/")
    reset_link = f"{frontend_url}/auth/password-reset?uid={uid}&token={token}"

    send_mail(
        subject="Restablecimiento de contraseña - DataPulse",
        message=(
            f"Hola {user.nombre_completo},\n\n"
            "Recibimos una solicitud para restablecer tu contraseña.\n"
            f"Usa el siguiente enlace (o los valores uid/token en la API):\n\n"
            f"{reset_link}\n\n"
            f"uid: {uid}\n"
            f"token: {token}\n\n"
            "Si no solicitaste este cambio, ignora este mensaje."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return GENERIC_RECOVERY_MESSAGE


def reset_password(*, uid: str, token: str, password: str) -> str | None:
    """
    Validate the reset token and set a new password for the user.

    Returns None on success or an error message in Spanish on failure.
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return "El enlace de restablecimiento no es válido."

    if not user.activo:
        return "La cuenta está desactivada."

    if not password_reset_token_generator.check_token(user, token):
        return "El token de restablecimiento no es válido o ha expirado."

    user.set_password(password)
    user.save(update_fields=["password"])
    return None
