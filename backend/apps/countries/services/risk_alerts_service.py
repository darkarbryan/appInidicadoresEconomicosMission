"""Shared helpers to recalculate IRPC and emit related alerts."""

from __future__ import annotations

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.countries.models import Country, EconomicIndicator, IndicatorType, RiskIndex
from apps.countries.services.irpc_service import guardar_irpc


def _latest_inflation(pais: Country) -> float | None:
    """Return the latest inflation percentage for a country, if any."""
    row = (
        EconomicIndicator.objects.filter(pais=pais, tipo=IndicatorType.INFLACION)
        .order_by("-anio")
        .first()
    )
    if not row:
        return None
    return float(row.valor)


def recalcular_irpc_con_alertas(*, countries=None) -> dict:
    """
    Recalculate IRPC for active countries and create business alerts.

    Alerts:
    - CRITICAL when IRPC < 25
    - WARNING when IRPC drops more than 15 points vs previous snapshot
    - CRITICAL when inflation > 50% (hyperinflation)
    """
    if countries is None:
        countries = Country.objects.filter(activo=True).order_by("codigo_iso")

    resultados = []
    alertas_creadas = 0

    for country in countries:
        previous = (
            RiskIndex.objects.filter(pais=country).order_by("-fecha_calculo").first()
        )
        previous_score = float(previous.indice_compuesto) if previous else None
        risk = guardar_irpc(country)
        current_score = float(risk.indice_compuesto)
        alerts = []

        if current_score < 25:
            Alert.objects.create(
                usuario=None,
                pais=country,
                tipo_alerta=AlertType.RIESGO,
                severidad=AlertSeverity.CRITICAL,
                titulo=f"IRPC crítico en {country.nombre}",
                mensaje=(
                    f"El IRPC de {country.codigo_iso} cayó a {current_score} "
                    f"(nivel {risk.nivel_riesgo})."
                ),
            )
            alertas_creadas += 1
            alerts.append("CRITICAL_IRPC_BAJO")

        if previous_score is not None and (previous_score - current_score) > 15:
            Alert.objects.create(
                usuario=None,
                pais=country,
                tipo_alerta=AlertType.RIESGO,
                severidad=AlertSeverity.WARNING,
                titulo=f"Caída significativa de IRPC en {country.nombre}",
                mensaje=(
                    f"El IRPC de {country.codigo_iso} bajó más de 15 puntos "
                    f"({previous_score} -> {current_score})."
                ),
            )
            alertas_creadas += 1
            alerts.append("WARNING_CAIDA_15")

        inflation = _latest_inflation(country)
        if inflation is not None and inflation > 50:
            Alert.objects.create(
                usuario=None,
                pais=country,
                tipo_alerta=AlertType.INDICADOR,
                severidad=AlertSeverity.CRITICAL,
                titulo=f"Hiperinflación en {country.nombre}",
                mensaje=(
                    f"La inflación de {country.codigo_iso} alcanza {inflation:.2f}% "
                    "(umbral crítico: 50%)."
                ),
            )
            alertas_creadas += 1
            alerts.append("CRITICAL_HIPERINFLACION")

        resultados.append(
            {
                "codigo_iso": country.codigo_iso,
                "indice_compuesto": current_score,
                "nivel_riesgo": risk.nivel_riesgo,
                "anterior": previous_score,
                "variacion": None
                if previous_score is None
                else round(current_score - previous_score, 2),
                "alertas": alerts,
            }
        )

    return {
        "paises_procesados": len(resultados),
        "alertas_creadas": alertas_creadas,
        "resultados": resultados,
    }
