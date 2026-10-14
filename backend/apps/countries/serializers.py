"""Serializers for countries, indicators and exchange-rate endpoints."""

from rest_framework import serializers

from apps.countries.models import Country, EconomicIndicator, ExchangeRate, RiskIndex


class CountrySerializer(serializers.ModelSerializer):
    """List/detail representation of a monitored country."""

    class Meta:
        model = Country
        fields = (
            "codigo_iso",
            "nombre",
            "moneda_codigo",
            "moneda_nombre",
            "region",
            "latitud",
            "longitud",
            "poblacion",
            "activo",
        )


class EconomicIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for economic indicator rows."""

    pais = serializers.CharField(source="pais_id", read_only=True)

    class Meta:
        model = EconomicIndicator
        fields = (
            "id",
            "pais",
            "tipo",
            "valor",
            "unidad",
            "anio",
            "fuente",
            "fecha_actualizacion",
        )


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for daily exchange-rate history."""

    moneda_origen = serializers.CharField(source="moneda_origen_id", read_only=True)

    class Meta:
        model = ExchangeRate
        fields = (
            "id",
            "moneda_origen",
            "moneda_destino",
            "tasa",
            "fecha",
            "variacion_porcentual",
            "fuente",
        )


class RiskIndexSummarySerializer(serializers.ModelSerializer):
    """Compact IRPC snapshot for country detail responses."""

    class Meta:
        model = RiskIndex
        fields = (
            "fecha_calculo",
            "score_economico",
            "score_cambiario",
            "score_estabilidad",
            "indice_compuesto",
            "nivel_riesgo",
        )


class CountryDetailSerializer(CountrySerializer):
    """Country detail including latest indicators and latest IRPC."""

    indicadores_recientes = serializers.SerializerMethodField()
    riesgo_actual = serializers.SerializerMethodField()

    class Meta(CountrySerializer.Meta):
        fields = CountrySerializer.Meta.fields + (
            "indicadores_recientes",
            "riesgo_actual",
        )

    def get_indicadores_recientes(self, obj):
        """Return the most recent indicator per type for the country."""
        latest_by_type = {}
        for indicator in obj.indicadores.order_by("-anio", "tipo"):
            if indicator.tipo not in latest_by_type:
                latest_by_type[indicator.tipo] = indicator
        return EconomicIndicatorSerializer(latest_by_type.values(), many=True).data

    def get_riesgo_actual(self, obj):
        """Return the latest calculated risk index, if any."""
        risk = obj.indices_riesgo.order_by("-fecha_calculo").first()
        if not risk:
            return None
        return RiskIndexSummarySerializer(risk).data
