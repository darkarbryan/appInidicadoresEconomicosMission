"""HTTP endpoints for portfolios, positions and summaries."""

from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from apiMission.pagination import StandardPagination
from apiMission.responses import error_response, ok_response
from apps.countries.models import RiskIndex
from apps.portfolios.models import Portfolio, Position
from apps.portfolios.permissions import CanManagePortfolios, IsPortfolioOwnerOrPublicRead
from apps.portfolios.serializers import (
    PortfolioDetailSerializer,
    PortfolioSerializer,
    PortfolioWriteSerializer,
    PositionSerializer,
    PositionWriteSerializer,
)
from apps.users.models import Rol


class PortfolioListCreateView(generics.ListCreateAPIView):
    """List own + public portfolios, or create a new portfolio."""

    permission_classes = [permissions.IsAuthenticated, CanManagePortfolios]
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "fecha_creacion", "fecha_modificacion"]
    ordering = ["-fecha_modificacion"]

    def get_serializer_class(self):
        """Use write serializer on create and list serializer otherwise."""
        if self.request.method == "POST":
            return PortfolioWriteSerializer
        return PortfolioSerializer

    def get_queryset(self):
        """Return portfolios owned by the user plus public active ones."""
        user = self.request.user
        queryset = Portfolio.objects.select_related("usuario").filter(
            Q(usuario=user) | Q(es_publico=True, activo=True)
        )
        if self.request.query_params.get("mios") == "1":
            queryset = queryset.filter(usuario=user)
        if self.request.query_params.get("publicos") == "1":
            queryset = queryset.filter(es_publico=True, activo=True)
        activo = self.request.query_params.get("activo")
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() in {"1", "true", "yes", "si", "sí"})
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        """Return paginated portfolios inside the standard envelope."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(PortfolioSerializer(page, many=True).data)
        return ok_response(PortfolioSerializer(queryset, many=True).data)

    def create(self, request, *args, **kwargs):
        """Create a portfolio owned by the authenticated user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        portfolio = serializer.save(usuario=request.user)
        return ok_response(
            PortfolioDetailSerializer(portfolio).data,
            http_status_code=status.HTTP_201_CREATED,
        )


class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or soft-delete a portfolio."""

    permission_classes = [
        permissions.IsAuthenticated,
        CanManagePortfolios,
        IsPortfolioOwnerOrPublicRead,
    ]
    lookup_field = "pk"
    http_method_names = ["get", "put", "delete", "head", "options"]

    def get_queryset(self):
        """Scope portfolios visible to the current user."""
        user = self.request.user
        if getattr(user, "rol", None) == Rol.ADMIN:
            return Portfolio.objects.select_related("usuario").prefetch_related("posiciones__pais")
        return (
            Portfolio.objects.select_related("usuario")
            .prefetch_related("posiciones__pais")
            .filter(Q(usuario=user) | Q(es_publico=True, activo=True))
        )

    def get_serializer_class(self):
        """Use write serializer for updates and detail serializer for reads."""
        if self.request.method == "PUT":
            return PortfolioWriteSerializer
        return PortfolioDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """Return portfolio detail with positions and metrics."""
        instance = self.get_object()
        return ok_response(PortfolioDetailSerializer(instance).data)

    def update(self, request, *args, **kwargs):
        """Update portfolio fields for the owner/admin."""
        instance = self.get_object()
        if instance.usuario_id != request.user.id and request.user.rol != Rol.ADMIN:
            return error_response(
                {"detail": "Solo el propietario puede editar este portafolio."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok_response(PortfolioDetailSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        """Soft-delete a portfolio by setting activo=False."""
        instance = self.get_object()
        if instance.usuario_id != request.user.id and request.user.rol != Rol.ADMIN:
            return error_response(
                {"detail": "Solo el propietario puede eliminar este portafolio."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )
        instance.activo = False
        instance.save(update_fields=["activo", "fecha_modificacion"])
        return ok_response({"detail": "Portafolio eliminado (soft delete).", "id": instance.id})


class PositionCreateView(APIView):
    """Add a position to a portfolio."""

    permission_classes = [permissions.IsAuthenticated, CanManagePortfolios]

    def post(self, request, pk):
        """Validate and create a position for the given portfolio."""
        portfolio = get_object_or_404(Portfolio, pk=pk, activo=True)
        if portfolio.usuario_id != request.user.id and request.user.rol != Rol.ADMIN:
            return error_response(
                {"detail": "Solo el propietario puede agregar posiciones."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = PositionWriteSerializer(
            data=request.data,
            context={"portafolio": portfolio, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        position = serializer.save(portafolio=portfolio)
        portfolio.fecha_modificacion = timezone.now()
        portfolio.save(update_fields=["fecha_modificacion"])
        return ok_response(
            PositionSerializer(position).data,
            http_status_code=status.HTTP_201_CREATED,
        )


class PositionDetailView(APIView):
    """Update or close a portfolio position."""

    permission_classes = [permissions.IsAuthenticated, CanManagePortfolios]

    def _get_owned_position(self, request, pk, position_id):
        """Return position if the requester can mutate the parent portfolio."""
        position = get_object_or_404(
            Position.objects.select_related("portafolio", "pais"),
            pk=position_id,
            portafolio_id=pk,
        )
        portfolio = position.portafolio
        if portfolio.usuario_id != request.user.id and request.user.rol != Rol.ADMIN:
            return None, error_response(
                {"detail": "Solo el propietario puede modificar posiciones."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )
        return position, None

    def put(self, request, pk, position_id):
        """Edit an existing position."""
        position, error = self._get_owned_position(request, pk, position_id)
        if error:
            return error
        serializer = PositionWriteSerializer(
            position,
            data=request.data,
            context={"portafolio": position.portafolio, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ok_response(PositionSerializer(position).data)

    def delete(self, request, pk, position_id):
        """Close a position by setting fecha_salida (soft close)."""
        position, error = self._get_owned_position(request, pk, position_id)
        if error:
            return error
        if position.fecha_salida:
            return error_response({"detail": "La posición ya está cerrada."})
        fecha_salida = request.data.get("fecha_salida") or date.today().isoformat()
        try:
            if isinstance(fecha_salida, str):
                cierre = date.fromisoformat(fecha_salida)
            else:
                cierre = fecha_salida
        except ValueError:
            return error_response({"detail": "fecha_salida inválida. Use formato YYYY-MM-DD."})
        if cierre <= position.fecha_entrada:
            return error_response(
                {"detail": "La fecha de salida debe ser posterior a la fecha de entrada."}
            )
        position.fecha_salida = cierre
        position.save(update_fields=["fecha_salida"])
        return ok_response(
            {
                "detail": "Posición cerrada correctamente.",
                "posicion": PositionSerializer(position).data,
            }
        )


class PortfolioSummaryView(APIView):
    """Return distribution and risk summary for a portfolio."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Aggregate open positions by country, asset type and weighted risk."""
        portfolio = get_object_or_404(
            Portfolio.objects.prefetch_related("posiciones__pais"),
            pk=pk,
        )
        if (
            portfolio.usuario_id != request.user.id
            and not (portfolio.es_publico and portfolio.activo)
            and request.user.rol != Rol.ADMIN
        ):
            return error_response(
                {"detail": "No tienes permiso para ver este portafolio."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )

        abiertas = [p for p in portfolio.posiciones.all() if p.fecha_salida is None]
        total = sum((p.monto_inversion_usd for p in abiertas), Decimal("0"))
        por_pais = {}
        por_tipo = {}
        riesgo_acum = Decimal("0")
        peso_riesgo = Decimal("0")

        for position in abiertas:
            por_pais[position.pais_id] = por_pais.get(position.pais_id, Decimal("0")) + (
                position.monto_inversion_usd
            )
            por_tipo[position.tipo_activo] = por_tipo.get(position.tipo_activo, Decimal("0")) + (
                position.monto_inversion_usd
            )
            risk = (
                RiskIndex.objects.filter(pais=position.pais)
                .order_by("-fecha_calculo")
                .first()
            )
            if risk:
                riesgo_acum += position.monto_inversion_usd * risk.indice_compuesto
                peso_riesgo += position.monto_inversion_usd

        return ok_response(
            {
                "portafolio_id": portfolio.id,
                "monto_total_usd": total,
                "distribucion_por_pais": [
                    {
                        "pais": codigo,
                        "monto_usd": monto,
                        "porcentaje": (
                            (monto / total * Decimal("100")).quantize(Decimal("0.01"))
                            if total
                            else Decimal("0")
                        ),
                    }
                    for codigo, monto in por_pais.items()
                ],
                "distribucion_por_tipo_activo": [
                    {
                        "tipo_activo": tipo,
                        "monto_usd": monto,
                        "porcentaje": (
                            (monto / total * Decimal("100")).quantize(Decimal("0.01"))
                            if total
                            else Decimal("0")
                        ),
                    }
                    for tipo, monto in por_tipo.items()
                ],
                "riesgo_promedio_ponderado": (
                    (riesgo_acum / peso_riesgo).quantize(Decimal("0.01"))
                    if peso_riesgo
                    else None
                ),
            }
        )


class PortfolioExportPdfView(APIView):
    """Placeholder for PDF export until reportlab/weasyprint is added."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """Return a structured export payload (PDF binary comes in a later pass)."""
        portfolio = get_object_or_404(Portfolio, pk=pk)
        if (
            portfolio.usuario_id != request.user.id
            and not (portfolio.es_publico and portfolio.activo)
            and request.user.rol != Rol.ADMIN
        ):
            return error_response(
                {"detail": "No tienes permiso para exportar este portafolio."},
                http_status_code=status.HTTP_403_FORBIDDEN,
            )
        detail = PortfolioDetailSerializer(portfolio).data
        return ok_response(
            {
                "detail": (
                    "Exportación PDF pendiente de librería de reportes. "
                    "Se devuelve el payload listo para renderizar."
                ),
                "formato": "json_preview",
                "portafolio": detail,
            }
        )
