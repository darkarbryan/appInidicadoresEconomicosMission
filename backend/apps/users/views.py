"""HTTP endpoints for authentication and user profile management."""

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apiMission.responses import error_response, ok_response
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.users.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordRecoverySerializer,
    PasswordResetSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UserSerializer,
)
from apps.users.services import auth_service


class RegisterView(APIView):
    """Create a new user account and return JWT tokens."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle user registration."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = serializer._tokens
        log_activity(
            usuario=user,
            accion=ActivityAction.CREAR,
            entidad_afectada="User",
            entidad_id=user.id,
            detalle={"email": user.email},
            request=request,
        )
        return ok_response(
            {
                "user": UserSerializer(user).data,
                "access": tokens["access"],
                "refresh": tokens["refresh"],
            },
            http_status_code=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle email/password login."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = auth_service.issue_tokens_for_user(user)
        log_activity(
            usuario=user,
            accion=ActivityAction.LOGIN,
            entidad_afectada="User",
            entidad_id=user.id,
            detalle={"email": user.email},
            request=request,
        )
        return ok_response(
            {
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
            }
        )


class MeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user profile."""

    http_method_names = ["get", "put", "head", "options"]

    def get_serializer_class(self):
        """Use a write serializer for updates and a read serializer for GET."""
        if self.request.method == "PUT":
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """Return the authenticated user profile inside the standard envelope."""
        instance = self.get_object()
        return ok_response(UserSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        """Update profile fields and return the full user representation."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok_response(UserSerializer(instance).data)


class PasswordRecoveryView(APIView):
    """Request a password-recovery email without revealing account existence."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Send recovery instructions when the account exists and is active."""
        serializer = PasswordRecoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = auth_service.request_password_recovery(
            email=serializer.validated_data["email"].lower().strip()
        )
        return ok_response({"detail": message})


class PasswordResetView(APIView):
    """Confirm a password reset using uid and token from the recovery email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Validate the reset token and set the new password."""
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        error = auth_service.reset_password(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            password=serializer.validated_data["password"],
        )
        if error:
            return error_response(
                {"detail": error},
                http_status_code=status.HTTP_400_BAD_REQUEST,
            )
        return ok_response({"detail": auth_service.PASSWORD_RESET_SUCCESS_MESSAGE})


class LogoutView(APIView):
    """Invalidate a refresh token to close the JWT session."""

    def post(self, request):
        """Blacklist the provided refresh token."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        error = auth_service.logout_user(refresh_token=serializer.validated_data["refresh"])
        if error:
            return error_response(
                {"detail": error},
                http_status_code=status.HTTP_400_BAD_REQUEST,
            )
        return ok_response({"detail": "Sesión cerrada correctamente."})


class AuthTokenRefreshView(TokenRefreshView):
    """Refresh an access token using a valid refresh token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Wrap the SimpleJWT refresh payload in the standard envelope."""
        response = super().post(request, *args, **kwargs)
        if response.status_code >= 400:
            return error_response(response.data, http_status_code=response.status_code)
        return ok_response(response.data)
