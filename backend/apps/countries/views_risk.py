"""HTTP endpoints for IRPC ranking, detail, history and recalculation."""

from datetime import datetime

from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from apiMission.pagination import StandardPagination
from apiMission.responses import ok_response, warning_response
from apps.countries.models import Country, RiskIndex
from apps.countries.serializers_risk import RiskIndexDetailSerializer, RiskRankingSerializer
from apps.countries.services.risk_alerts_service import recalcular_irpc_con_alertas
from apps.users.permissions import IsAdminRole


def _latest_risk_queryset():
    """Return one latest RiskIndex row per country."""
    latest_ids = (
        RiskIndex.objects.filter(pais=OuterRef("pais"))
        .order_by("-fecha_calculo", "-id")
        .values("id")[:1]
    )
    return (
        RiskIndex.objects.filter(id=Subquery(latest_ids))
        .select_related("pais")
        .order_by("-indice_compuesto", "pais_id")
    )


class RiskRankingView(generics.ListAPIView):
    """Rank countries by their latest composite risk index."""

    serializer_class = RiskRankingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["pais__nombre", "pais__codigo_iso"]
    ordering_fields = ["indice_compuesto", "nivel_riesgo", "fecha_calculo"]
    ordering = ["-indice_compuesto"]

    def get_queryset(self):
        """Optionally filter ranking by risk level or region."""
        queryset = _latest_risk_queryset()
        nivel = self.request.query_params.get("nivel_riesgo")
        region = self.request.query_params.get("region")
        if nivel:
            queryset = queryset.filter(nivel_riesgo=nivel.upper())
        if region:
            queryset = queryset.filter(pais__region=region.upper())
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated ranking inside the standard envelope."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return ok_response(self.get_serializer(queryset, many=True).data)


class RiskCountryDetailView(APIView):
    """Return current IRPC and a short history for one country."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, codigo_iso):
        """Build detail payload with current score and recent history."""
        country = get_object_or_404(Country, codigo_iso=codigo_iso.upper())
        history = list(
            RiskIndex.objects.filter(pais=country).order_by("-fecha_calculo")[:20]
        )
        actual = history[0] if history else None
        return ok_response(
            {
                "pais": {
                    "codigo_iso": country.codigo_iso,
                    "nombre": country.nombre,
                    "region": country.region,
                    "bandera_url": country.bandera_url,
                },
                "actual": RiskIndexDetailSerializer(actual).data if actual else None,
                "historico": RiskIndexDetailSerializer(history, many=True).data,
            }
        )


class RiskHistoryView(generics.ListAPIView):
    """List IRPC history for a country with optional date range filters."""

    serializer_class = RiskIndexDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["fecha_calculo", "indice_compuesto"]
    ordering = ["-fecha_calculo"]

    def get_country(self):
        """Resolve country from codigo_iso path param."""
        return get_object_or_404(Country, codigo_iso=self.kwargs["codigo_iso"].upper())

    def get_queryset(self):
        """Filter history by fecha_desde/fecha_hasta when provided."""
        country = self.get_country()
        queryset = RiskIndex.objects.filter(pais=country)
        fecha_desde = self.request.query_params.get("fecha_desde")
        fecha_hasta = self.request.query_params.get("fecha_hasta")
        if fecha_desde:
            try:
                queryset = queryset.filter(
                    fecha_calculo__date__gte=datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                )
            except ValueError:
                queryset = queryset.none()
        if fecha_hasta:
            try:
                queryset = queryset.filter(
                    fecha_calculo__date__lte=datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                )
            except ValueError:
                queryset = queryset.none()
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated history inside the standard envelope."""
        self.get_country()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return ok_response(self.get_serializer(queryset, many=True).data)


class RiskRecalculateView(APIView):
    """Recalculate IRPC for all active countries (ADMIN only)."""

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        """Recalculate scores, persist snapshots and emit risk alerts."""
        summary = recalcular_irpc_con_alertas()
        payload = {
            "detail": "Recálculo de IRPC completado.",
            "fecha": timezone.now().isoformat(),
            **summary,
        }
        if summary["alertas_creadas"]:
            return warning_response(payload)
        return ok_response(payload)
