"""Management command: sync World Bank indicators and recalculate IRPC."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.countries.services.risk_alerts_service import recalcular_irpc_con_alertas
from apps.countries.services.sync_service import sync_indicadores_world_bank


class Command(BaseCommand):
    """Synchronize economic indicators and chain IRPC recalculation."""

    help = "Sincroniza indicadores desde World Bank y recalcula IRPC con alertas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--years",
            type=int,
            default=5,
            help="Cantidad de años a sincronizar (1-15).",
        )
        parser.add_argument(
            "--skip-irpc",
            action="store_true",
            help="No recalcular IRPC después del sync.",
        )

    def handle(self, *args, **options):
        years = options["years"]
        if years < 1 or years > 15:
            self.stderr.write(self.style.ERROR("years debe estar entre 1 y 15."))
            return

        self.stdout.write(f"[{timezone.now():%Y-%m-%d %H:%M:%S}] Iniciando sync World Bank...")
        summary = sync_indicadores_world_bank(years=years)
        self.stdout.write(f"  -> Países procesados: {summary['paises_procesados']}")
        self.stdout.write(f"  -> Indicadores upserted: {summary['indicadores_upserted']}")
        self.stdout.write(f"  -> Errores: {len(summary['errores'])}")

        if options["skip_irpc"]:
            self.stdout.write(self.style.WARNING("Recálculo IRPC omitido (--skip-irpc)."))
            return

        self.stdout.write("Recalculando IRPC...")
        risk = recalcular_irpc_con_alertas()
        self.stdout.write(f"  -> Países IRPC: {risk['paises_procesados']}")
        self.stdout.write(f"  -> Alertas creadas: {risk['alertas_creadas']}")
        self.stdout.write(self.style.SUCCESS("Sync + IRPC finalizado."))
