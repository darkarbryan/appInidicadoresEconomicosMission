"""Management command: enrich countries via REST Countries API."""

from django.core.management.base import BaseCommand

from apps.countries.services.restcountries_service import sync_countries_from_restcountries


class Command(BaseCommand):
    """Pull population, coordinates and flag URLs from REST Countries."""

    help = "Enriquece países existentes con datos de REST Countries (bandera, población, coords)."

    def handle(self, *args, **options):
        summary = sync_countries_from_restcountries()
        self.stdout.write(f"  -> Procesados: {summary['paises_procesados']}")
        self.stdout.write(f"  -> Actualizados: {summary['paises_actualizados']}")
        self.stdout.write(f"  -> Errores: {len(summary['errores'])}")
        self.stdout.write(self.style.SUCCESS("REST Countries sync finalizado."))
