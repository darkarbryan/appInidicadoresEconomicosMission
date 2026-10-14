"""Serializers for country risk (IRPC) endpoints."""

from rest_framework import serializers

from apps.countries.models import RiskIndex


class RiskRankingSerializer(serializers.ModelSerializer):
    """Latest IRPC row enriched with country display fields."""

    codigo_iso = serializers.CharField(source="pais_id", read_only=True)
    nombre = serializers.CharField(source="pais.nombre", read_only=True)
    region = serializers.CharField(source="pais.region", read_only=True)

    class Meta:
        model = RiskIndex
        fields = (
            "codigo_iso",
            "nombre",
            "region",
            "fecha_calculo",
            "score_economico",
            "score_cambiario",
            "score_estabilidad",
            "indice_compuesto",
            "nivel_riesgo",
        )


class RiskIndexDetailSerializer(serializers.ModelSerializer):
    """Full IRPC snapshot including calculation breakdown."""

    codigo_iso = serializers.CharField(source="pais_id", read_only=True)

    class Meta:
        model = RiskIndex
        fields = (
            "id",
            "codigo_iso",
            "fecha_calculo",
            "score_economico",
            "score_cambiario",
            "score_estabilidad",
            "indice_compuesto",
            "nivel_riesgo",
            "detalle_calculo",
        )
