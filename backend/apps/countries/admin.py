from django.contrib import admin

from apps.countries.models import Country, EconomicIndicator, ExchangeRate, RiskIndex


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin configuration for Country."""

    list_display = (
        "codigo_iso",
        "nombre",
        "moneda_codigo",
        "region",
        "poblacion",
        "activo",
    )
    list_filter = ("region", "activo")
    search_fields = ("codigo_iso", "nombre", "moneda_codigo")
    ordering = ("nombre",)


@admin.register(EconomicIndicator)
class EconomicIndicatorAdmin(admin.ModelAdmin):
    """Admin configuration for EconomicIndicator."""

    list_display = ("pais", "tipo", "anio", "valor", "unidad", "fuente", "fecha_actualizacion")
    list_filter = ("tipo", "fuente", "anio", "unidad")
    search_fields = ("pais__codigo_iso", "pais__nombre")
    autocomplete_fields = ("pais",)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin configuration for ExchangeRate."""

    list_display = (
        "moneda_origen",
        "moneda_destino",
        "tasa",
        "fecha",
        "variacion_porcentual",
        "fuente",
    )
    list_filter = ("moneda_destino", "fuente", "fecha")
    search_fields = ("moneda_origen__moneda_codigo", "moneda_origen__nombre")
    autocomplete_fields = ("moneda_origen",)
    date_hierarchy = "fecha"


@admin.register(RiskIndex)
class RiskIndexAdmin(admin.ModelAdmin):
    """Admin configuration for RiskIndex."""

    list_display = (
        "pais",
        "fecha_calculo",
        "indice_compuesto",
        "nivel_riesgo",
        "score_economico",
        "score_cambiario",
        "score_estabilidad",
    )
    list_filter = ("nivel_riesgo",)
    search_fields = ("pais__codigo_iso", "pais__nombre")
    autocomplete_fields = ("pais",)
    date_hierarchy = "fecha_calculo"
