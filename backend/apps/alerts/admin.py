from django.contrib import admin

from apps.alerts.models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    """Admin configuration for Alert."""

    list_display = (
        "titulo",
        "pais",
        "usuario",
        "tipo_alerta",
        "severidad",
        "leida",
        "fecha_creacion",
    )
    list_filter = ("tipo_alerta", "severidad", "leida")
    search_fields = ("titulo", "mensaje", "pais__codigo_iso", "usuario__email")
    autocomplete_fields = ("usuario", "pais")
    date_hierarchy = "fecha_creacion"
