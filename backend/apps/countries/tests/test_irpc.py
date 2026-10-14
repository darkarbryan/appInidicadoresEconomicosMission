"""Unit tests for IRPC classification and hyperinflation alerts."""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.countries.models import (
    Country,
    EconomicIndicator,
    IndicatorSource,
    IndicatorType,
    IndicatorUnit,
    Region,
    RiskLevel,
)
from apps.countries.services.irpc_service import clasificar_nivel_riesgo
from apps.countries.services.risk_alerts_service import recalcular_irpc_con_alertas


class IrpcClassificationTests(TestCase):
    """Verify IRPC score-to-level mapping from the tech statement."""

    def test_clasificar_nivel_riesgo(self):
        self.assertEqual(clasificar_nivel_riesgo(80), RiskLevel.BAJO)
        self.assertEqual(clasificar_nivel_riesgo(60), RiskLevel.MODERADO)
        self.assertEqual(clasificar_nivel_riesgo(30), RiskLevel.ALTO)
        self.assertEqual(clasificar_nivel_riesgo(10), RiskLevel.CRITICO)


class HyperinflationAlertTests(TestCase):
    """Ensure inflation above 50% creates a CRITICAL indicator alert."""

    def setUp(self):
        self.country = Country.objects.create(
            codigo_iso="ZZ",
            nombre="Pais Test",
            moneda_codigo="ZZD",
            moneda_nombre="Zeta",
            region=Region.ANDINA,
            latitud=Decimal("1.000000"),
            longitud=Decimal("-1.000000"),
            poblacion=1000,
            activo=True,
        )
        EconomicIndicator.objects.create(
            pais=self.country,
            tipo=IndicatorType.INFLACION,
            valor=Decimal("55.0000"),
            unidad=IndicatorUnit.PORCENTAJE,
            anio=timezone.now().year,
            fuente=IndicatorSource.MANUAL,
        )

    def test_hyperinflation_creates_critical_alert(self):
        summary = recalcular_irpc_con_alertas(countries=[self.country])
        self.assertGreaterEqual(summary["alertas_creadas"], 1)
        alert = Alert.objects.filter(
            pais=self.country,
            tipo_alerta=AlertType.INDICADOR,
            severidad=AlertSeverity.CRITICAL,
            titulo__icontains="Hiperinflación",
        ).first()
        self.assertIsNotNone(alert)
