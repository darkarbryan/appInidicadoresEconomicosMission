from django.contrib import admin

from apps.activity.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin configuration for ActivityLog."""

    list_display = (
        "usuario",
        "accion",
        "entidad_afectada",
        "entidad_id",
        "ip_address",
        "fecha",
    )
    list_filter = ("accion", "entidad_afectada")
    search_fields = ("usuario__email", "entidad_afectada", "entidad_id")
    autocomplete_fields = ("usuario",)
    date_hierarchy = "fecha"
    readonly_fields = (
        "usuario",
        "accion",
        "entidad_afectada",
        "entidad_id",
        "detalle",
        "ip_address",
        "fecha",
    )
