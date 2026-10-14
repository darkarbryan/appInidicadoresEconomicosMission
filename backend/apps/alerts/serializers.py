"""Serializers for alert endpoints."""

from rest_framework import serializers

from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """Public representation of an alert."""

    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)

    class Meta:
        model = Alert
        fields = (
            "id",
            "usuario",
            "pais",
            "pais_nombre",
            "tipo_alerta",
            "severidad",
            "titulo",
            "mensaje",
            "leida",
            "fecha_creacion",
        )
        read_only_fields = fields
