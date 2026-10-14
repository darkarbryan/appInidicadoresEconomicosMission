"""Helpers to persist activity audit records."""

from __future__ import annotations

from typing import Any

from apps.activity.models import ActivityAction, ActivityLog


def get_client_ip(request) -> str | None:
    """Extract the client IP from common proxy/forwarded headers."""
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(
    *,
    usuario,
    accion: str,
    entidad_afectada: str,
    entidad_id: str | int = "",
    detalle: dict[str, Any] | None = None,
    request=None,
) -> ActivityLog | None:
    """
    Persist an activity log row when a user is available.

    Returns None when usuario is anonymous/missing.
    """
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return None

    return ActivityLog.objects.create(
        usuario=usuario,
        accion=accion,
        entidad_afectada=entidad_afectada,
        entidad_id=str(entidad_id) if entidad_id is not None else "",
        detalle=detalle or {},
        ip_address=get_client_ip(request),
    )


# Re-export action constants for convenient imports.
__all__ = ["ActivityAction", "get_client_ip", "log_activity"]
