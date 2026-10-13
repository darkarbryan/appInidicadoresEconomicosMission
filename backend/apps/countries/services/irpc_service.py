"""Country risk index (IRPC) calculation following the technical test formulas."""

from __future__ import annotations

from decimal import Decimal
from statistics import pstdev
from typing import Any

from django.utils import timezone

from apps.countries.models import (
    Country,
    EconomicIndicator,
    ExchangeRate,
    IndicatorType,
    RiskIndex,
    RiskLevel,
)


def _to_float(value) -> float | None:
    """Convert Decimal/numeric values to float; return None when missing."""
    if value is None:
        return None
    return float(value)


def _latest_indicator(pais: Country, tipo: str) -> float | None:
    """Return the latest indicator value for a country and type."""
    indicator = (
        EconomicIndicator.objects.filter(pais=pais, tipo=tipo)
        .order_by("-anio")
        .first()
    )
    return _to_float(indicator.valor) if indicator else None


def _indicator_for_year(pais: Country, tipo: str, anio: int) -> float | None:
    """Return an indicator value for a specific year."""
    indicator = EconomicIndicator.objects.filter(pais=pais, tipo=tipo, anio=anio).first()
    return _to_float(indicator.valor) if indicator else None


def _count_negative_indicators(pais: Country) -> int:
    """Count latest indicators that fall into risk thresholds."""
    count = 0
    inflacion = _latest_indicator(pais, IndicatorType.INFLACION)
    desempleo = _latest_indicator(pais, IndicatorType.DESEMPLEO)
    deuda = _latest_indicator(pais, IndicatorType.DEUDA_PIB)
    balanza = _latest_indicator(pais, IndicatorType.BALANZA_COMERCIAL)
    pib_pc = _latest_indicator(pais, IndicatorType.PIB_PERCAPITA)

    if inflacion is not None and inflacion > 5:
        count += 1
    if desempleo is not None and desempleo > 7:
        count += 1
    if deuda is not None and deuda > 50:
        count += 1
    if balanza is not None and balanza < 0:
        count += 1
    if pib_pc is not None and pib_pc < 12000:
        count += 1
    return count


def calcular_score_economico(pais: Country) -> tuple[float, dict[str, Any]]:
    """Calculate the economic score (0-100) and its breakdown."""
    score = 100.0
    detalle: dict[str, Any] = {"penalizaciones": []}

    pib_pc = _latest_indicator(pais, IndicatorType.PIB_PERCAPITA)
    if pib_pc is not None:
        if pib_pc < 3000:
            score -= 30
            detalle["penalizaciones"].append({"motivo": "PIB_PERCAPITA", "valor": pib_pc, "penalizacion": 30})
        elif pib_pc < 6000:
            score -= 15
            detalle["penalizaciones"].append({"motivo": "PIB_PERCAPITA", "valor": pib_pc, "penalizacion": 15})
        elif pib_pc < 12000:
            score -= 5
            detalle["penalizaciones"].append({"motivo": "PIB_PERCAPITA", "valor": pib_pc, "penalizacion": 5})
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["PIB_PERCAPITA"]

    inflacion = _latest_indicator(pais, IndicatorType.INFLACION)
    if inflacion is not None:
        if inflacion > 50:
            score -= 40
            detalle["penalizaciones"].append({"motivo": "INFLACION", "valor": inflacion, "penalizacion": 40})
        elif inflacion > 10:
            score -= 25
            detalle["penalizaciones"].append({"motivo": "INFLACION", "valor": inflacion, "penalizacion": 25})
        elif inflacion > 5:
            score -= 10
            detalle["penalizaciones"].append({"motivo": "INFLACION", "valor": inflacion, "penalizacion": 10})
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["INFLACION"]

    desempleo = _latest_indicator(pais, IndicatorType.DESEMPLEO)
    if desempleo is not None:
        if desempleo > 15:
            score -= 25
            detalle["penalizaciones"].append({"motivo": "DESEMPLEO", "valor": desempleo, "penalizacion": 25})
        elif desempleo > 10:
            score -= 15
            detalle["penalizaciones"].append({"motivo": "DESEMPLEO", "valor": desempleo, "penalizacion": 15})
        elif desempleo > 7:
            score -= 5
            detalle["penalizaciones"].append({"motivo": "DESEMPLEO", "valor": desempleo, "penalizacion": 5})
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["DESEMPLEO"]

    deuda = _latest_indicator(pais, IndicatorType.DEUDA_PIB)
    if deuda is not None:
        if deuda > 80:
            score -= 20
            detalle["penalizaciones"].append({"motivo": "DEUDA_PIB", "valor": deuda, "penalizacion": 20})
        elif deuda > 50:
            score -= 10
            detalle["penalizaciones"].append({"motivo": "DEUDA_PIB", "valor": deuda, "penalizacion": 10})
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["DEUDA_PIB"]

    score = max(0.0, score)
    detalle["score"] = score
    return score, detalle


def calcular_score_cambiario(pais: Country, dias: int = 30) -> tuple[float, dict[str, Any]]:
    """Calculate the FX score (0-100) using recent daily variations."""
    score = 100.0
    detalle: dict[str, Any] = {"penalizaciones": []}

    rates = list(
        ExchangeRate.objects.filter(moneda_origen=pais)
        .order_by("-fecha")[:dias]
        .values_list("variacion_porcentual", flat=True)
    )
    variaciones = [_to_float(v) for v in rates if v is not None]

    if len(variaciones) >= 2:
        volatilidad = pstdev(variaciones)
        detalle["volatilidad"] = volatilidad
        if volatilidad > 3.0:
            score -= 40
            detalle["penalizaciones"].append({"motivo": "VOLATILIDAD", "valor": volatilidad, "penalizacion": 40})
        elif volatilidad > 1.5:
            score -= 25
            detalle["penalizaciones"].append({"motivo": "VOLATILIDAD", "valor": volatilidad, "penalizacion": 25})
        elif volatilidad > 0.5:
            score -= 10
            detalle["penalizaciones"].append({"motivo": "VOLATILIDAD", "valor": volatilidad, "penalizacion": 10})

        depreciacion = sum(variaciones)
        detalle["depreciacion_acumulada"] = depreciacion
        if depreciacion > 10:
            score -= 30
            detalle["penalizaciones"].append({"motivo": "DEPRECIACION", "valor": depreciacion, "penalizacion": 30})
        elif depreciacion > 5:
            score -= 15
            detalle["penalizaciones"].append({"motivo": "DEPRECIACION", "valor": depreciacion, "penalizacion": 15})
        elif depreciacion > 2:
            score -= 5
            detalle["penalizaciones"].append({"motivo": "DEPRECIACION", "valor": depreciacion, "penalizacion": 5})
    else:
        detalle["faltantes"] = ["VARIACIONES_TIPO_CAMBIO"]

    score = max(0.0, score)
    detalle["score"] = score
    return score, detalle


def calcular_score_estabilidad(pais: Country) -> tuple[float, dict[str, Any]]:
    """Calculate the stability score (0-100) and its breakdown."""
    score = 100.0
    detalle: dict[str, Any] = {"penalizaciones": []}

    balanza = _latest_indicator(pais, IndicatorType.BALANZA_COMERCIAL)
    if balanza is not None:
        if balanza < -10:
            score -= 25
            detalle["penalizaciones"].append({"motivo": "BALANZA_COMERCIAL", "valor": balanza, "penalizacion": 25})
        elif balanza < -5:
            score -= 15
            detalle["penalizaciones"].append({"motivo": "BALANZA_COMERCIAL", "valor": balanza, "penalizacion": 15})
        elif balanza < 0:
            score -= 5
            detalle["penalizaciones"].append({"motivo": "BALANZA_COMERCIAL", "valor": balanza, "penalizacion": 5})
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["BALANZA_COMERCIAL"]

    latest_pib = (
        EconomicIndicator.objects.filter(pais=pais, tipo=IndicatorType.PIB)
        .order_by("-anio")
        .first()
    )
    if latest_pib:
        pib_actual = _to_float(latest_pib.valor)
        pib_anterior = _indicator_for_year(pais, IndicatorType.PIB, latest_pib.anio - 1)
        if pib_actual is not None and pib_anterior and pib_anterior != 0:
            crecimiento = ((pib_actual - pib_anterior) / pib_anterior) * 100
            detalle["crecimiento_pib"] = crecimiento
            if crecimiento < -2:
                score -= 30
                detalle["penalizaciones"].append({"motivo": "CRECIMIENTO_PIB", "valor": crecimiento, "penalizacion": 30})
            elif crecimiento < 0:
                score -= 20
                detalle["penalizaciones"].append({"motivo": "CRECIMIENTO_PIB", "valor": crecimiento, "penalizacion": 20})
            elif crecimiento < 1:
                score -= 10
                detalle["penalizaciones"].append({"motivo": "CRECIMIENTO_PIB", "valor": crecimiento, "penalizacion": 10})
        else:
            detalle["faltantes"] = detalle.get("faltantes", []) + ["PIB_ANTERIOR"]
    else:
        detalle["faltantes"] = detalle.get("faltantes", []) + ["PIB"]

    negativos = _count_negative_indicators(pais)
    if negativos:
        score -= negativos * 5
        detalle["penalizaciones"].append(
            {"motivo": "INDICADORES_NEGATIVOS", "valor": negativos, "penalizacion": negativos * 5}
        )
    detalle["indicadores_negativos"] = negativos

    score = max(0.0, score)
    detalle["score"] = score
    return score, detalle


def clasificar_nivel_riesgo(irpc: float) -> str:
    """Map an IRPC score to its risk level label."""
    if irpc >= 75:
        return RiskLevel.BAJO
    if irpc >= 50:
        return RiskLevel.MODERADO
    if irpc >= 25:
        return RiskLevel.ALTO
    return RiskLevel.CRITICO


def calcular_irpc(pais: Country) -> dict[str, Any]:
    """
    Calculate the full IRPC payload for a country.

    IRPC = score_economico * 0.40 + score_cambiario * 0.30 + score_estabilidad * 0.30
    """
    score_economico, det_eco = calcular_score_economico(pais)
    score_cambiario, det_cam = calcular_score_cambiario(pais)
    score_estabilidad, det_est = calcular_score_estabilidad(pais)

    irpc = (score_economico * 0.40) + (score_cambiario * 0.30) + (score_estabilidad * 0.30)
    irpc = max(0.0, min(100.0, irpc))
    nivel = clasificar_nivel_riesgo(irpc)

    return {
        "score_economico": Decimal(str(round(score_economico, 2))),
        "score_cambiario": Decimal(str(round(score_cambiario, 2))),
        "score_estabilidad": Decimal(str(round(score_estabilidad, 2))),
        "indice_compuesto": Decimal(str(round(irpc, 2))),
        "nivel_riesgo": nivel,
        "detalle_calculo": {
            "formula": "IRPC = economico*0.40 + cambiario*0.30 + estabilidad*0.30",
            "economico": det_eco,
            "cambiario": det_cam,
            "estabilidad": det_est,
            "faltantes": list(
                {
                    *(det_eco.get("faltantes", [])),
                    *(det_cam.get("faltantes", [])),
                    *(det_est.get("faltantes", [])),
                }
            ),
        },
    }


def guardar_irpc(pais: Country) -> RiskIndex:
    """Calculate IRPC for a country and persist a RiskIndex row."""
    payload = calcular_irpc(pais)
    return RiskIndex.objects.create(
        pais=pais,
        fecha_calculo=timezone.now(),
        score_economico=payload["score_economico"],
        score_cambiario=payload["score_cambiario"],
        score_estabilidad=payload["score_estabilidad"],
        indice_compuesto=payload["indice_compuesto"],
        nivel_riesgo=payload["nivel_riesgo"],
        detalle_calculo=payload["detalle_calculo"],
    )
