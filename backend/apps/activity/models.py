"""Domain model for auditing user activity on the platform."""

from django.conf import settings
from django.db import models


class ActivityAction(models.TextChoices):
    """Auditable actions recorded in the activity log."""

    CREAR = "CREAR", "Crear"
    EDITAR = "EDITAR", "Editar"
    ELIMINAR = "ELIMINAR", "Eliminar"
    CONSULTAR = "CONSULTAR", "Consultar"
    LOGIN = "LOGIN", "Login"
    EXPORT = "EXPORT", "Export"


class ActivityLog(models.Model):
    """Immutable-style record of a user action against a domain entity."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="logs_actividad",
        verbose_name="usuario",
    )
    accion = models.CharField("acción", max_length=20, choices=ActivityAction.choices)
    entidad_afectada = models.CharField("entidad afectada", max_length=100)
    entidad_id = models.CharField("id de entidad", max_length=64, blank=True)
    detalle = models.JSONField("detalle", default=dict, blank=True)
    ip_address = models.GenericIPAddressField("dirección IP", null=True, blank=True)
    fecha = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        db_table = "logs_actividad"
        verbose_name = "log de actividad"
        verbose_name_plural = "logs de actividad"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["usuario", "-fecha"], name="idx_log_usuario_fecha"),
            models.Index(
                fields=["entidad_afectada", "entidad_id"],
                name="idx_log_entidad",
            ),
            models.Index(fields=["accion"], name="idx_log_accion"),
        ]

    def __str__(self):
        return f"{self.usuario_id} {self.accion} {self.entidad_afectada}"
