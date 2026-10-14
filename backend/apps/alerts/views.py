"""HTTP endpoints for user and global alerts."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView

from apiMission.pagination import StandardPagination
from apiMission.responses import ok_response
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertSerializer


class AlertListView(generics.ListAPIView):
    """List alerts visible to the authenticated user."""

    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["fecha_creacion", "severidad", "tipo_alerta"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        """Return personal alerts plus global alerts (usuario is null)."""
        user = self.request.user
        queryset = Alert.objects.select_related("pais", "usuario").filter(
            Q(usuario=user) | Q(usuario__isnull=True)
        )
        leida = self.request.query_params.get("leida")
        tipo = self.request.query_params.get("tipo")
        severidad = self.request.query_params.get("severidad")
        if leida is not None:
            queryset = queryset.filter(leida=leida.lower() in {"1", "true", "yes", "si", "sí"})
        if tipo:
            queryset = queryset.filter(tipo_alerta=tipo.upper())
        if severidad:
            queryset = queryset.filter(severidad=severidad.upper())
        return queryset

    def list(self, request, *args, **kwargs):
        """Return paginated alerts inside the standard envelope."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return ok_response(self.get_serializer(queryset, many=True).data)


class AlertMarkReadView(APIView):
    """Mark a single alert as read."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        """Set leida=True for an alert visible to the current user."""
        alert = get_object_or_404(
            Alert.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True)),
            pk=pk,
        )
        alert.leida = True
        alert.save(update_fields=["leida"])
        return ok_response(AlertSerializer(alert).data)


class AlertMarkAllReadView(APIView):
    """Mark all visible unread alerts as read."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        """Bulk-update unread alerts for the authenticated user."""
        updated = (
            Alert.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True), leida=False)
            .update(leida=True)
        )
        return ok_response({"detail": "Alertas marcadas como leídas.", "actualizadas": updated})


class AlertSummaryView(APIView):
    """Return alert counts grouped by type and severity."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Aggregate visible alerts for dashboard badges."""
        queryset = Alert.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
        por_tipo = (
            queryset.values("tipo_alerta")
            .annotate(total=Count("id"), no_leidas=Count("id", filter=Q(leida=False)))
            .order_by("tipo_alerta")
        )
        por_severidad = (
            queryset.values("severidad")
            .annotate(total=Count("id"), no_leidas=Count("id", filter=Q(leida=False)))
            .order_by("severidad")
        )
        return ok_response(
            {
                "total": queryset.count(),
                "no_leidas": queryset.filter(leida=False).count(),
                "por_tipo": list(por_tipo),
                "por_severidad": list(por_severidad),
            }
        )
