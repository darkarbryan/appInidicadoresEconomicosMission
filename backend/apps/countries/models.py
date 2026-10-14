"""Domain models for countries, economic indicators, FX rates and risk indexes."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Region(models.TextChoices):
    """Latin American regions used to classify countries."""

    ANDINA = "ANDINA", "Andina"
    CONO_SUR = "CONO_SUR", "Cono Sur"
    CENTROAMERICA = "CENTROAMERICA", "Centroamérica"
    CARIBE = "CARIBE", "Caribe"


class IndicatorType(models.TextChoices):
    """Supported economic indicator types."""

    PIB = "PIB", "PIB"
    INFLACION = "INFLACION", "Inflación"
    DESEMPLEO = "DESEMPLEO", "Desempleo"
    BALANZA_COMERCIAL = "BALANZA_COMERCIAL", "Balanza comercial"
    DEUDA_PIB = "DEUDA_PIB", "Deuda / PIB"
    PIB_PERCAPITA = "PIB_PERCAPITA", "PIB per cápita"


class IndicatorUnit(models.TextChoices):
    """Measurement units for economic indicators."""

    PORCENTAJE = "PORCENTAJE", "Porcentaje"
    USD = "USD", "USD"
    USD_MILES_MILLONES = "USD_MILES_MILLONES", "USD miles de millones"


class IndicatorSource(models.TextChoices):
    """Data sources for economic indicators."""

    WORLD_BANK = "WORLD_BANK", "World Bank"
    MANUAL = "MANUAL", "Manual"


class RiskLevel(models.TextChoices):
    """Composite country risk classification levels."""

    BAJO = "BAJO", "Bajo"
    MODERADO = "MODERADO", "Moderado"
    ALTO = "ALTO", "Alto"
    CRITICO = "CRITICO", "Crítico"


class Country(models.Model):
    """Country monitored by the DataPulse platform."""

    codigo_iso = models.CharField("código ISO", max_length=2, primary_key=True)
    nombre = models.CharField("nombre", max_length=100)
    moneda_codigo = models.CharField("código de moneda", max_length=3, unique=True)
    moneda_nombre = models.CharField("nombre de moneda", max_length=100)
    region = models.CharField("región", max_length=20, choices=Region.choices)
    latitud = models.DecimalField("latitud", max_digits=9, decimal_places=6)
    longitud = models.DecimalField("longitud", max_digits=9, decimal_places=6)
    poblacion = models.BigIntegerField("población", null=True, blank=True)
    bandera_url = models.URLField("URL de bandera", max_length=500, blank=True, default="")
    activo = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "paises"
        verbose_name = "país"
        verbose_name_plural = "países"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_iso})"


class EconomicIndicator(models.Model):
    """Economic indicator value for a country in a given year."""

    pais = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="indicadores",
        verbose_name="país",
    )
    tipo = models.CharField("tipo", max_length=30, choices=IndicatorType.choices)
    valor = models.DecimalField("valor", max_digits=20, decimal_places=4)
    unidad = models.CharField("unidad", max_length=30, choices=IndicatorUnit.choices)
    anio = models.PositiveIntegerField("año")
    fuente = models.CharField(
        "fuente",
        max_length=20,
        choices=IndicatorSource.choices,
        default=IndicatorSource.WORLD_BANK,
    )
    fecha_actualizacion = models.DateTimeField("fecha de actualización", auto_now=True)

    class Meta:
        db_table = "indicadores_economicos"
        verbose_name = "indicador económico"
        verbose_name_plural = "indicadores económicos"
        ordering = ["-anio", "tipo"]
        constraints = [
            models.UniqueConstraint(
                fields=["pais", "tipo", "anio"],
                name="uq_indicador_pais_tipo_anio",
            ),
        ]
        indexes = [
            models.Index(fields=["pais", "tipo"], name="idx_indicador_pais_tipo"),
            models.Index(fields=["anio"], name="idx_indicador_anio"),
        ]

    def __str__(self):
        return f"{self.pais_id} {self.tipo} {self.anio}"


class ExchangeRate(models.Model):
    """Daily exchange rate for a local currency against a destination currency."""

    moneda_origen = models.ForeignKey(
        Country,
        to_field="moneda_codigo",
        db_column="moneda_origen",
        on_delete=models.CASCADE,
        related_name="tipos_cambio",
        verbose_name="moneda origen",
    )
    moneda_destino = models.CharField("moneda destino", max_length=3, default="USD")
    tasa = models.DecimalField("tasa", max_digits=20, decimal_places=8)
    fecha = models.DateField("fecha")
    variacion_porcentual = models.DecimalField(
        "variación porcentual",
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
    )
    fuente = models.CharField("fuente", max_length=50, default="EXCHANGE_RATE_API")

    class Meta:
        db_table = "tipos_cambio"
        verbose_name = "tipo de cambio"
        verbose_name_plural = "tipos de cambio"
        ordering = ["-fecha"]
        indexes = [
            models.Index(
                fields=["moneda_origen", "fecha"],
                name="idx_tipo_cambio_moneda_fecha",
            ),
        ]

    def __str__(self):
        return f"{self.moneda_origen_id}/{self.moneda_destino} {self.fecha}"


class RiskIndex(models.Model):
    """Calculated country risk index (IRPC) snapshot."""

    pais = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="indices_riesgo",
        verbose_name="país",
    )
    fecha_calculo = models.DateTimeField("fecha de cálculo")
    score_economico = models.DecimalField(
        "score económico",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    score_cambiario = models.DecimalField(
        "score cambiario",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    score_estabilidad = models.DecimalField(
        "score estabilidad",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    indice_compuesto = models.DecimalField(
        "índice compuesto",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    nivel_riesgo = models.CharField(
        "nivel de riesgo",
        max_length=20,
        choices=RiskLevel.choices,
    )
    detalle_calculo = models.JSONField("detalle de cálculo", default=dict, blank=True)

    class Meta:
        db_table = "indices_riesgo"
        verbose_name = "índice de riesgo"
        verbose_name_plural = "índices de riesgo"
        ordering = ["-fecha_calculo"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(indice_compuesto__gte=0)
                & models.Q(indice_compuesto__lte=100),
                name="chk_indice_compuesto_rango",
            ),
        ]
        indexes = [
            models.Index(fields=["pais", "-fecha_calculo"], name="idx_riesgo_pais_fecha"),
            models.Index(fields=["nivel_riesgo"], name="idx_riesgo_nivel"),
        ]

    def __str__(self):
        return f"{self.pais_id} IRPC={self.indice_compuesto} ({self.fecha_calculo:%Y-%m-%d})"
