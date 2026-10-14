"""Synchronization of economic indicators from the World Bank API."""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.countries.models import (
    Country,
    EconomicIndicator,
    IndicatorSource,
    IndicatorType,
    IndicatorUnit,
)

logger = logging.getLogger(__name__)

WORLD_BANK_BASE = "https://api.worldbank.org/v2"
WORLD_BANK_INDICATORS = {
    IndicatorType.PIB: ("NY.GDP.MKTP.CD", IndicatorUnit.USD),
    IndicatorType.INFLACION: ("FP.CPI.TOTL.ZG", IndicatorUnit.PORCENTAJE),
    IndicatorType.DESEMPLEO: ("SL.UEM.TOTL.ZS", IndicatorUnit.PORCENTAJE),
    IndicatorType.BALANZA_COMERCIAL: ("NE.RSB.GNFS.ZS", IndicatorUnit.PORCENTAJE),
    IndicatorType.DEUDA_PIB: ("GC.DOD.TOTL.GD.ZS", IndicatorUnit.PORCENTAJE),
    IndicatorType.PIB_PERCAPITA: ("NY.GDP.PCAP.CD", IndicatorUnit.USD),
}


def _fetch_indicator(codigo_iso: str, wb_code: str, date_range: str) -> list[dict]:
    """
    Fetch one World Bank indicator series for a country.

    Returns an empty list when the remote API fails or returns no usable rows.
    """
    url = f"{WORLD_BANK_BASE}/country/{codigo_iso}/indicator/{wb_code}"
    params = {"date": date_range, "format": "json", "per_page": 100}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error(
            "World Bank request failed country=%s indicator=%s error=%s",
            codigo_iso,
            wb_code,
            exc,
        )
        return []

    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        return []
    return payload[1]


def sync_indicadores_world_bank(*, years: int = 5) -> dict:
    """
    Synchronize indicators for all active countries from World Bank.

    Continues processing remaining countries when one country/indicator fails.
    """
    current_year = timezone.now().year
    date_range = f"{current_year - years + 1}:{current_year}"
    countries = list(Country.objects.filter(activo=True).order_by("codigo_iso"))

    summary = {
        "inicio": timezone.now().isoformat(),
        "paises_procesados": 0,
        "indicadores_upserted": 0,
        "errores": [],
        "paises": [],
    }

    logger.info("Starting World Bank sync for %s countries", len(countries))

    for country in countries:
        country_result = {
            "codigo_iso": country.codigo_iso,
            "upserted": 0,
            "errores": [],
        }
        for tipo, (wb_code, unidad) in WORLD_BANK_INDICATORS.items():
            rows = _fetch_indicator(country.codigo_iso, wb_code, date_range)
            if not rows:
                message = (
                    f"Sin datos o error de API para {country.codigo_iso}/{tipo} ({wb_code})"
                )
                country_result["errores"].append(message)
                summary["errores"].append(message)
                continue

            for row in rows:
                value = row.get("value")
                year = row.get("date")
                if value is None or year is None:
                    continue
                try:
                    anio = int(year)
                    valor = Decimal(str(value))
                except (TypeError, ValueError, InvalidOperation):
                    continue

                _, created = EconomicIndicator.objects.update_or_create(
                    pais=country,
                    tipo=tipo,
                    anio=anio,
                    defaults={
                        "valor": valor,
                        "unidad": unidad,
                        "fuente": IndicatorSource.WORLD_BANK,
                    },
                )
                country_result["upserted"] += 1
                summary["indicadores_upserted"] += 1
                if created:
                    logger.debug(
                        "Created indicator %s %s %s",
                        country.codigo_iso,
                        tipo,
                        anio,
                    )

        summary["paises_procesados"] += 1
        summary["paises"].append(country_result)
        logger.info(
            "Finished country=%s upserted=%s errors=%s",
            country.codigo_iso,
            country_result["upserted"],
            len(country_result["errores"]),
        )

    summary["fin"] = timezone.now().isoformat()

    first_country = countries[0] if countries else None
    if first_country:
        Alert.objects.create(
            usuario=None,
            pais=first_country,
            tipo_alerta=AlertType.INDICADOR,
            severidad=AlertSeverity.INFO,
            titulo="Datos económicos actualizados",
            mensaje=(
                "Se sincronizaron indicadores desde World Bank. "
                f"Países procesados: {summary['paises_procesados']}. "
                f"Indicadores upserted: {summary['indicadores_upserted']}."
            ),
            leida=False,
        )

    logger.info(
        "World Bank sync finished processed=%s upserted=%s errors=%s",
        summary["paises_procesados"],
        summary["indicadores_upserted"],
        len(summary["errores"]),
    )
    return summary
