"""
Management command to synchronize FX rates from ExchangeRate-API.

Usage:
    python manage.py sync_tipos_cambio
"""

from django.core.management.base import BaseCommand

from apps.countries.services.fx_sync_service import sync_tipos_cambio


class Command(BaseCommand):
    """Pull daily FX rates and store variations with optional alerts."""

    help = "Sincroniza tipos de cambio desde ExchangeRate-API para los 10 países."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("SYNC TIPOS DE CAMBIO"))
        self.stdout.write("Fuente: https://api.exchangerate-api.com/v4/latest/USD")

        summary = sync_tipos_cambio()

        self.stdout.write(f"  -> Paises procesados: {summary['paises_procesados']}")
        self.stdout.write(f"  -> Tasas upserted:    {summary['tasas_upserted']}")
        self.stdout.write(f"  -> Alertas creadas:   {summary['alertas_creadas']}")
        self.stdout.write(f"  -> Errores:           {len(summary['errores'])}")

        for error in summary["errores"]:
            self.stdout.write(self.style.WARNING(f"  [WARN] {error}"))

        for item in summary.get("detalle", []):
            if item.get("error"):
                continue
            self.stdout.write(
                f"  [OK] {item['codigo_iso']} {item['moneda']}: "
                f"tasa={item.get('tasa')} var={item.get('variacion_porcentual')}%"
            )

        if summary["errores"] and summary["tasas_upserted"] == 0:
            self.stdout.write(self.style.ERROR("Sincronizacion fallida."))
            return

        self.stdout.write(self.style.SUCCESS("Sincronizacion FX finalizada."))
