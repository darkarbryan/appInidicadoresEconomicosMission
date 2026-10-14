"""Synchronization of FX rates from ExchangeRate-API."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import requests
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.countries.models import Country, ExchangeRate

logger = logging.getLogger(__name__)

EXCHANGE_RATE_URL = "https://api.exchangerate-api.com/v4/latest/USD"
VARIATION_ALERT_THRESHOLD = Decimal("3.0")


def sync_tipos_cambio() -> dict:
    """
    Fetch USD-based rates and store one daily row per active country currency.

    Calculates variation versus the previous stored day and emits WARNING alerts
    when absolute daily variation exceeds 3%.
    """
    summary = {
        "inicio": timezone.now().isoformat(),
        "fecha": date.today().isoformat(),
        "paises_procesados": 0,
        "tasas_upserted": 0,
        "alertas_creadas": 0,
        "errores": [],
        "detalle": [],
    }

    try:
        response = requests.get(EXCHANGE_RATE_URL, timeout=20)
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates") or {}
    except (requests.RequestException, ValueError) as exc:
        message = f"ExchangeRate-API no disponible: {exc}"
        logger.error(message)
        summary["errores"].append(message)
        summary["fin"] = timezone.now().isoformat()
        return summary

    today = date.today()
    yesterday = today - timedelta(days=1)
    countries = Country.objects.filter(activo=True).order_by("codigo_iso")

    for country in countries:
        codigo = country.moneda_codigo
        raw_rate = rates.get(codigo)
        country_result = {"codigo_iso": country.codigo_iso, "moneda": codigo}

        if raw_rate is None:
            message = f"Sin tasa para {country.codigo_iso}/{codigo}"
            summary["errores"].append(message)
            country_result["error"] = message
            summary["detalle"].append(country_result)
            summary["paises_procesados"] += 1
            continue

        try:
            # API returns units of local currency per 1 USD.
            # Persist as local-per-USD to stay consistent with seed FX rows.
            tasa = Decimal(str(raw_rate)).quantize(Decimal("0.00000001"))
        except (InvalidOperation, TypeError, ValueError):
            message = f"Tasa inválida para {codigo}: {raw_rate}"
            summary["errores"].append(message)
            country_result["error"] = message
            summary["detalle"].append(country_result)
            summary["paises_procesados"] += 1
            continue

        previous = (
            ExchangeRate.objects.filter(
                moneda_origen=country,
                moneda_destino="USD",
                fecha__lt=today,
            )
            .order_by("-fecha")
            .first()
        )
        if previous and previous.tasa:
            variacion = ((tasa - previous.tasa) / previous.tasa * Decimal("100")).quantize(
                Decimal("0.0001")
            )
        else:
            # Fallback: try exact yesterday row if present.
            yday = ExchangeRate.objects.filter(
                moneda_origen=country,
                moneda_destino="USD",
                fecha=yesterday,
            ).first()
            if yday and yday.tasa:
                variacion = ((tasa - yday.tasa) / yday.tasa * Decimal("100")).quantize(
                    Decimal("0.0001")
                )
            else:
                variacion = Decimal("0.0000")

        obj, created = ExchangeRate.objects.update_or_create(
            moneda_origen=country,
            moneda_destino="USD",
            fecha=today,
            defaults={
                "tasa": tasa,
                "variacion_porcentual": variacion,
                "fuente": "EXCHANGE_RATE_API",
            },
        )
        summary["tasas_upserted"] += 1
        summary["paises_procesados"] += 1
        country_result.update(
            {
                "tasa": str(tasa),
                "variacion_porcentual": str(variacion),
                "created": created,
            }
        )

        if abs(variacion) > VARIATION_ALERT_THRESHOLD:
            Alert.objects.create(
                usuario=None,
                pais=country,
                tipo_alerta=AlertType.TIPO_CAMBIO,
                severidad=AlertSeverity.WARNING,
                titulo=f"Variación FX > 3% en {country.nombre}",
                mensaje=(
                    f"La variación diaria de {codigo}/USD es {variacion}% "
                    f"(umbral {VARIATION_ALERT_THRESHOLD}%)."
                ),
            )
            summary["alertas_creadas"] += 1
            country_result["alerta"] = "WARNING_FX_3"

        summary["detalle"].append(country_result)
        logger.info(
            "FX sync country=%s currency=%s rate=%s variation=%s",
            country.codigo_iso,
            codigo,
            tasa,
            variacion,
        )

    summary["fin"] = timezone.now().isoformat()
    return summary
