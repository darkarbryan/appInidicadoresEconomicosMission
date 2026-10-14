"""Synchronize country metadata from the REST Countries API."""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

import requests

from apps.countries.models import Country

logger = logging.getLogger(__name__)

REST_COUNTRIES_BASE = "https://restcountries.com/v3.1"


def _to_decimal(value) -> Decimal | None:
    """Convert a numeric value to Decimal, or None when invalid."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def sync_countries_from_restcountries(*, only_active: bool = True) -> dict:
    """
    Enrich existing Country rows with population, coordinates and flag URL.

    Uses ISO alpha-2 codes already stored in the database.
    Continues when one country request fails.
    """
    queryset = Country.objects.all().order_by("codigo_iso")
    if only_active:
        queryset = queryset.filter(activo=True)

    countries = list(queryset)
    summary = {
        "paises_procesados": 0,
        "paises_actualizados": 0,
        "errores": [],
        "paises": [],
    }

    for country in countries:
        result = {"codigo_iso": country.codigo_iso, "actualizado": False, "error": None}
        url = f"{REST_COUNTRIES_BASE}/alpha/{country.codigo_iso}"
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            payload = response.json()
            data = payload[0] if isinstance(payload, list) else payload
        except (requests.RequestException, ValueError, IndexError, TypeError) as exc:
            message = f"REST Countries falló para {country.codigo_iso}: {exc}"
            logger.error(message)
            result["error"] = message
            summary["errores"].append(message)
            summary["paises"].append(result)
            summary["paises_procesados"] += 1
            continue

        changed = False
        population = data.get("population")
        if population is not None and country.poblacion != population:
            country.poblacion = population
            changed = True

        latlng = data.get("latlng") or []
        if len(latlng) >= 2:
            lat = _to_decimal(latlng[0])
            lon = _to_decimal(latlng[1])
            if lat is not None and country.latitud != lat:
                country.latitud = lat
                changed = True
            if lon is not None and country.longitud != lon:
                country.longitud = lon
                changed = True

        flags = data.get("flags") or {}
        flag_url = flags.get("svg") or flags.get("png") or ""
        if flag_url and country.bandera_url != flag_url:
            country.bandera_url = flag_url
            changed = True

        if changed:
            country.save()
            result["actualizado"] = True
            summary["paises_actualizados"] += 1

        summary["paises_procesados"] += 1
        summary["paises"].append(result)
        logger.info(
            "REST Countries iso=%s updated=%s",
            country.codigo_iso,
            result["actualizado"],
        )

    return summary
