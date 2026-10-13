"""Serializers for authentication and user profile endpoints."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from apps.users.models import User
from apps.users.services import auth_service


class UserSerializer(serializers.ModelSerializer):
    """Public representation of the authenticated user profile."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "nombre_completo",
            "rol",
            "activo",
            "fecha_creacion",
        )
        read_only_fields = ("id", "email", "rol", "activo", "fecha_creacion")


class RegisterSerializer(serializers.Serializer):
    """Payload validation for user registration."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    nombre_completo = serializers.CharField(max_length=255)

    def validate_email(self, value):
        """Ensure the email is not already registered."""
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario con este email.")
        return email

    def validate(self, attrs):
        """Validate password confirmation and Django password rules."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        """Register the user and attach issued JWT tokens to the instance context."""
        user, tokens = auth_service.register_user(
            email=validated_data["email"],
            password=validated_data["password"],
            nombre_completo=validated_data["nombre_completo"].strip(),
        )
        self._tokens = tokens
        return user


class LoginSerializer(serializers.Serializer):
    """Payload validation for email/password login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate credentials and attach the user to validated data."""
        user, error = auth_service.authenticate_user(
            email=attrs["email"].lower().strip(),
            password=attrs["password"],
        )
        if error:
            raise AuthenticationFailed(error)
        attrs["user"] = user
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Allow the authenticated user to update editable profile fields."""

    class Meta:
        model = User
        fields = ("nombre_completo",)

    def validate_nombre_completo(self, value):
        """Reject empty full-name values."""
        nombre = value.strip()
        if not nombre:
            raise serializers.ValidationError("El nombre completo es obligatorio.")
        return nombre


class PasswordRecoverySerializer(serializers.Serializer):
    """Payload validation for password-recovery requests."""

    email = serializers.EmailField()


class PasswordResetSerializer(serializers.Serializer):
    """Payload validation for confirming a password reset."""

    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        """Validate password confirmation and Django password rules."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Payload validation for JWT logout (refresh token blacklist)."""

    refresh = serializers.CharField()
