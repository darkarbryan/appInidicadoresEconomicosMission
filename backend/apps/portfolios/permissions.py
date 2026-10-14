"""Portfolio-specific permission helpers."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.users.models import Rol


class CanManagePortfolios(BasePermission):
    """VIEWER can read; only ANALISTA/ADMIN can create or mutate portfolios."""

    message = "Un usuario VIEWER no puede crear ni editar portafolios."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(user, "rol", None) in {Rol.ADMIN, Rol.ANALISTA}


class IsPortfolioOwnerOrPublicRead(BasePermission):
    """Allow owners full access; others may only read public portfolios."""

    message = "No tienes permiso para acceder a este portafolio."

    def has_object_permission(self, request, view, obj):
        if obj.usuario_id == request.user.id:
            return True
        if request.method in SAFE_METHODS and obj.es_publico and obj.activo:
            return True
        return getattr(request.user, "rol", None) == Rol.ADMIN
