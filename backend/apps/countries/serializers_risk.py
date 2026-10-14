"""Serializers for country risk (IRPC) endpoints."""

from rest_framework import serializers

from apps.countries.models import RiskIndex


class RiskRankingSerializer(serializers.ModelSerializer):
    """Latest IRPC row enriched with country display fields and variation."""

    codigo_iso = serializers.CharField(source="pais_id", read_only=True)
    nombre = serializers.CharField(source="pais.nombre", read_only=True)
    region = serializers.CharField(source="pais.region", read_only=True)
    variacion = serializers.SerializerMethodField()
    tendencia = serializers.SerializerMethodField()

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
            "variacion",
            "tendencia",
        )

    def _previous_score(self, obj) -> float | None:
        """Return the previous IRPC score for the same country, if any."""
        previous = (
            RiskIndex.objects.filter(pais_id=obj.pais_id)
            .exclude(id=obj.id)
            .order_by("-fecha_calculo", "-id")
            .first()
        )
        if not previous:
            return None
        return float(previous.indice_compuesto)

    def get_variacion(self, obj) -> float | None:
        """Delta of current IRPC vs previous calculation."""
        previous = self._previous_score(obj)
        if previous is None:
            return None
        return round(float(obj.indice_compuesto) - previous, 2)

    def get_tendencia(self, obj) -> str:
        """Up / down / stable trend label based on IRPC variation."""
        variacion = self.get_variacion(obj)
        if variacion is None:
            return "ESTABLE"
        if variacion > 0.5:
            return "ALCISTA"
        if variacion < -0.5:
            return "BAJISTA"
        return "ESTABLE"


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
