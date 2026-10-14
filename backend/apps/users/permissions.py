"""Role-based permission classes for the DataPulse API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.users.models import Rol


class IsAdminRole(BasePermission):
    """Allow access only to authenticated users with ADMIN role."""

    message = "Se requiere rol ADMIN para realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "rol", None) == Rol.ADMIN
        )


class IsAnalistaOrAdmin(BasePermission):
    """Allow ANALISTA and ADMIN roles for write operations."""

    message = "Se requiere rol ANALISTA o ADMIN para realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "rol", None) in {Rol.ADMIN, Rol.ANALISTA}
