"""HTTP endpoints for countries, indicators and exchange rates."""

from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from apiMission.pagination import StandardPagination
from apiMission.responses import error_response, ok_response, warning_response
from apps.countries.models import Country, EconomicIndicator, ExchangeRate
from apps.countries.serializers import (
    CountryDetailSerializer,
    CountrySerializer,
    EconomicIndicatorSerializer,
    ExchangeRateSerializer,
)
from apps.activity.models import ActivityAction
from apps.activity.services import log_activity
from apps.countries.services.fx_sync_service import sync_tipos_cambio
from apps.countries.services.sync_service import sync_indicadores_world_bank
from apps.users.permissions import IsAdminRole


class CountryListView(generics.ListAPIView):
    """List monitored countries with region filter, search and ordering."""

    serializer_class = CountrySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "codigo_iso", "moneda_codigo"]
    ordering_fields = ["nombre", "codigo_iso", "region", "poblacion"]
    ordering = ["nombre"]

    def get_queryset(self):
        """Return active countries, optionally filtered by region."""
        queryset = Country.objects.all()
        region = self.request.query_params.get("region")
        activo = self.request.query_params.get("activo")

        if region:
            queryset = queryset.filter(region=region.upper())
        if activo is not None:
            value = activo.lower() in {"1", "true", "yes", "si", "sí"}
            queryset = queryset.filter(activo=value)
        else:
            queryset = queryset.filter(activo=True)
        return queryset

    def list(self, request, *args, **kwargs):
        """Return the paginated country list inside the standard envelope."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ok_response(serializer.data)


class CountryDetailView(generics.RetrieveAPIView):
    """Retrieve one country with latest indicators and current IRPC."""

    serializer_class = CountryDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "codigo_iso"
    queryset = Country.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """Return country detail wrapped in the standard envelope."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ok_response(serializer.data)


class CountryIndicatorsView(generics.ListAPIView):
    """List economic indicators for a country with optional filters."""

    serializer_class = EconomicIndicatorSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["anio", "tipo", "valor", "fecha_actualizacion"]
    ordering = ["-anio", "tipo"]

    def get_country(self):
        """Resolve the country from the URL codigo_iso."""
        return get_object_or_404(Country, codigo_iso=self.kwargs["codigo_iso"].upper())

    def get_queryset(self):
        """Return indicators for the country filtered by tipo/anio when provided."""
        country = self.get_country()
        queryset = EconomicIndicator.objects.filter(pais=country)

        tipo = self.request.query_params.get("tipo")
        anio = self.request.query_params.get("anio")
        if tipo:
            queryset = queryset.filter(tipo=tipo.upper())
        if anio:
            try:
                queryset = queryset.filter(anio=int(anio))
            except (TypeError, ValueError):
                queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated indicators inside the standard envelope."""
        self.get_country()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ok_response(serializer.data)


class CountryExchangeRateView(generics.ListAPIView):
    """List FX history for a country currency with optional date range."""

    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["fecha", "tasa", "variacion_porcentual"]
    ordering = ["-fecha"]

    def get_country(self):
        """Resolve the country from the URL codigo_iso."""
        return get_object_or_404(Country, codigo_iso=self.kwargs["codigo_iso"].upper())

    def get_queryset(self):
        """Return FX rows for the country currency, filtered by fecha range."""
        country = self.get_country()
        queryset = ExchangeRate.objects.filter(moneda_origen=country)

        fecha_desde = self.request.query_params.get("fecha_desde")
        fecha_hasta = self.request.query_params.get("fecha_hasta")

        if fecha_desde:
            try:
                queryset = queryset.filter(
                    fecha__gte=datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                )
            except ValueError:
                queryset = queryset.none()
        if fecha_hasta:
            try:
                queryset = queryset.filter(
                    fecha__lte=datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                )
            except ValueError:
                queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated FX history inside the standard envelope."""
        self.get_country()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return ok_response(serializer.data)


class SyncIndicatorsView(APIView):
    """Trigger World Bank indicator synchronization (ADMIN only)."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        """
        Synchronize indicators for all active countries.

        Continues on per-country API failures and returns a structured summary.
        """
        years = request.data.get("years", 5)
        try:
            years = int(years)
            if years < 1 or years > 15:
                raise ValueError
        except (TypeError, ValueError):
            return error_response(
                {"detail": "El parámetro years debe ser un entero entre 1 y 15."}
            )

        summary = sync_indicadores_world_bank(years=years)
        log_activity(
            usuario=request.user,
            accion=ActivityAction.EDITAR,
            entidad_afectada="EconomicIndicator",
            entidad_id="sync",
            detalle={"years": years, "upserted": summary.get("indicadores_upserted")},
            request=request,
        )
        if summary["errores"]:
            return warning_response(
                {
                    "detail": "Sincronización finalizada con errores parciales.",
                    "resumen": summary,
                }
            )
        return ok_response(
            {
                "detail": "Sincronización de indicadores completada.",
                "resumen": summary,
            }
        )


class SyncExchangeRatesView(APIView):
    """Trigger FX synchronization from ExchangeRate-API (ADMIN only)."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        """Synchronize daily FX rates and emit variation alerts when needed."""
        summary = sync_tipos_cambio()
        log_activity(
            usuario=request.user,
            accion=ActivityAction.EDITAR,
            entidad_afectada="ExchangeRate",
            entidad_id="sync",
            detalle={
                "tasas_upserted": summary.get("tasas_upserted"),
                "alertas_creadas": summary.get("alertas_creadas"),
            },
            request=request,
        )
        if summary["errores"] and summary["tasas_upserted"] == 0:
            return error_response(
                {
                    "detail": "No se pudo sincronizar tipos de cambio.",
                    "resumen": summary,
                }
            )
        if summary["errores"]:
            return warning_response(
                {
                    "detail": "Sincronización FX finalizada con errores parciales.",
                    "resumen": summary,
                }
            )
        return ok_response(
            {
                "detail": "Sincronización de tipos de cambio completada.",
                "resumen": summary,
            }
        )
