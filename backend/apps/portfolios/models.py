"""Domain models for investment portfolios and positions."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.countries.models import Country


class AssetType(models.TextChoices):
    """Supported investment asset types inside a portfolio."""

    RENTA_FIJA = "RENTA_FIJA", "Renta fija"
    RENTA_VARIABLE = "RENTA_VARIABLE", "Renta variable"
    COMMODITIES = "COMMODITIES", "Commodities"
    MONEDA = "MONEDA", "Moneda"


class Portfolio(models.Model):
    """Investment portfolio owned by a platform user."""

    nombre = models.CharField("nombre", max_length=100)
    descripcion = models.TextField("descripción", blank=True, max_length=500)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portafolios",
        verbose_name="usuario",
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    fecha_modificacion = models.DateTimeField("fecha de modificación", auto_now=True)
    activo = models.BooleanField("activo", default=True)
    es_publico = models.BooleanField("es público", default=False)

    class Meta:
        db_table = "portafolios"
        verbose_name = "portafolio"
        verbose_name_plural = "portafolios"
        ordering = ["-fecha_modificacion"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nombre"],
                name="uq_portafolio_usuario_nombre",
            ),
        ]
        indexes = [
            models.Index(fields=["usuario", "activo"], name="idx_portafolio_usuario"),
            models.Index(fields=["es_publico"], name="idx_portafolio_publico"),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.usuario_id})"


class Position(models.Model):
    """Investment position belonging to a portfolio."""

    portafolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="posiciones",
        verbose_name="portafolio",
    )
    pais = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="posiciones",
        verbose_name="país",
    )
    tipo_activo = models.CharField(
        "tipo de activo",
        max_length=20,
        choices=AssetType.choices,
    )
    monto_inversion_usd = models.DecimalField(
        "monto inversión USD",
        max_digits=14,
        decimal_places=2,
    )
    fecha_entrada = models.DateField("fecha de entrada")
    fecha_salida = models.DateField("fecha de salida", null=True, blank=True)
    notas = models.CharField("notas", max_length=200, blank=True)

    class Meta:
        db_table = "posiciones"
        verbose_name = "posición"
        verbose_name_plural = "posiciones"
        ordering = ["-fecha_entrada"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(fecha_salida__isnull=True)
                    | models.Q(fecha_salida__gt=models.F("fecha_entrada"))
                ),
                name="chk_posicion_fecha_salida",
            ),
        ]
        indexes = [
            models.Index(
                fields=["portafolio", "pais", "tipo_activo"],
                name="idx_posicion_port_pais_tipo",
            ),
        ]

    def __str__(self):
        return f"{self.portafolio_id} {self.pais_id} {self.tipo_activo}"

    def clean(self):
        """Validate exit date is after entry date when provided."""
        super().clean()
        if self.fecha_salida and self.fecha_entrada and self.fecha_salida <= self.fecha_entrada:
            raise ValidationError(
                {"fecha_salida": "La fecha de salida debe ser posterior a la fecha de entrada."}
            )
