from django.contrib import admin

from apps.portfolios.models import Portfolio, Position


class PositionInline(admin.TabularInline):
    """Inline editor for portfolio positions."""

    model = Position
    extra = 0
    autocomplete_fields = ("pais",)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Admin configuration for Portfolio."""

    list_display = (
        "nombre",
        "usuario",
        "es_publico",
        "activo",
        "fecha_creacion",
        "fecha_modificacion",
    )
    list_filter = ("activo", "es_publico")
    search_fields = ("nombre", "usuario__email", "descripcion")
    autocomplete_fields = ("usuario",)
    inlines = (PositionInline,)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position."""

    list_display = (
        "portafolio",
        "pais",
        "tipo_activo",
        "monto_inversion_usd",
        "fecha_entrada",
        "fecha_salida",
    )
    list_filter = ("tipo_activo", "pais")
    search_fields = ("portafolio__nombre", "pais__codigo_iso", "notas")
    autocomplete_fields = ("portafolio", "pais")
