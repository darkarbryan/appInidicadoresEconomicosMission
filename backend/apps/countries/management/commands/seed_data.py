"""
Seed command for DataPulse technical-test baseline data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from random import Random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.alerts.models import Alert, AlertSeverity, AlertType
from apps.countries.models import (
    Country,
    EconomicIndicator,
    ExchangeRate,
    IndicatorSource,
    IndicatorType,
    IndicatorUnit,
    Region,
    RiskIndex,
)
from apps.countries.services.irpc_service import guardar_irpc
from apps.portfolios.models import AssetType, Portfolio, Position
from apps.users.models import Rol, User

SEED_PASSWORD = "DataPulse2026!"
YEARS = (2022, 2023, 2024)
FX_DAYS = 30
RNG = Random(42)

COUNTRIES = [
    {
        "codigo_iso": "CO",
        "nombre": "Colombia",
        "moneda_codigo": "COP",
        "moneda_nombre": "Peso colombiano",
        "region": Region.ANDINA,
        "latitud": "4.570900",
        "longitud": "-74.297300",
        "poblacion": 51520000,
        "fx_base": Decimal("4100.00000000"),
    },
    {
        "codigo_iso": "BR",
        "nombre": "Brasil",
        "moneda_codigo": "BRL",
        "moneda_nombre": "Real brasileño",
        "region": Region.CONO_SUR,
        "latitud": "-14.235000",
        "longitud": "-51.925300",
        "poblacion": 215300000,
        "fx_base": Decimal("5.10000000"),
    },
    {
        "codigo_iso": "MX",
        "nombre": "México",
        "moneda_codigo": "MXN",
        "moneda_nombre": "Peso mexicano",
        "region": Region.CENTROAMERICA,
        "latitud": "23.634500",
        "longitud": "-102.552800",
        "poblacion": 128900000,
        "fx_base": Decimal("17.20000000"),
    },
    {
        "codigo_iso": "AR",
        "nombre": "Argentina",
        "moneda_codigo": "ARS",
        "moneda_nombre": "Peso argentino",
        "region": Region.CONO_SUR,
        "latitud": "-38.416100",
        "longitud": "-63.616700",
        "poblacion": 46000000,
        "fx_base": Decimal("950.00000000"),
    },
    {
        "codigo_iso": "CL",
        "nombre": "Chile",
        "moneda_codigo": "CLP",
        "moneda_nombre": "Peso chileno",
        "region": Region.CONO_SUR,
        "latitud": "-35.675100",
        "longitud": "-71.543000",
        "poblacion": 19600000,
        "fx_base": Decimal("930.00000000"),
    },
    {
        "codigo_iso": "PE",
        "nombre": "Perú",
        "moneda_codigo": "PEN",
        "moneda_nombre": "Sol peruano",
        "region": Region.ANDINA,
        "latitud": "-9.190000",
        "longitud": "-75.015200",
        "poblacion": 34000000,
        "fx_base": Decimal("3.75000000"),
    },
    {
        "codigo_iso": "EC",
        "nombre": "Ecuador",
        "moneda_codigo": "USD",
        "moneda_nombre": "Dólar estadounidense",
        "region": Region.ANDINA,
        "latitud": "-1.831200",
        "longitud": "-78.183400",
        "poblacion": 18000000,
        "fx_base": Decimal("1.00000000"),
    },
    {
        "codigo_iso": "UY",
        "nombre": "Uruguay",
        "moneda_codigo": "UYU",
        "moneda_nombre": "Peso uruguayo",
        "region": Region.CONO_SUR,
        "latitud": "-32.522800",
        "longitud": "-55.765800",
        "poblacion": 3500000,
        "fx_base": Decimal("39.50000000"),
    },
    {
        "codigo_iso": "PY",
        "nombre": "Paraguay",
        "moneda_codigo": "PYG",
        "moneda_nombre": "Guaraní paraguayo",
        "region": Region.CONO_SUR,
        "latitud": "-23.442500",
        "longitud": "-58.443800",
        "poblacion": 7400000,
        "fx_base": Decimal("7300.00000000"),
    },
    {
        "codigo_iso": "PA",
        "nombre": "Panamá",
        "moneda_codigo": "PAB",
        "moneda_nombre": "Balboa panameño",
        "region": Region.CENTROAMERICA,
        "latitud": "8.538000",
        "longitud": "-80.782100",
        "poblacion": 4400000,
        "fx_base": Decimal("1.00000000"),
    },
]

# Plausible baseline values used to generate 3 years of indicators (seed/manual).
INDICATOR_BASE = {
    "CO": {
        IndicatorType.PIB: (340_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (9.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (11.3, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-4.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (55.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (6800, IndicatorUnit.USD),
    },
    "BR": {
        IndicatorType.PIB: (1_900_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (4.6, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (8.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (1.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (74.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (8900, IndicatorUnit.USD),
    },
    "MX": {
        IndicatorType.PIB: (1_400_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (5.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (3.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-1.1, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (48.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (11000, IndicatorUnit.USD),
    },
    "AR": {
        IndicatorType.PIB: (640_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (120.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (7.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (2.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (88.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (13500, IndicatorUnit.USD),
    },
    "CL": {
        IndicatorType.PIB: (300_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (4.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (8.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (0.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (38.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (15500, IndicatorUnit.USD),
    },
    "PE": {
        IndicatorType.PIB: (240_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (3.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (6.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-1.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (34.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (7100, IndicatorUnit.USD),
    },
    "EC": {
        IndicatorType.PIB: (115_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (2.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (4.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-0.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (52.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (6400, IndicatorUnit.USD),
    },
    "UY": {
        IndicatorType.PIB: (70_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (6.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (8.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-2.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (62.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (19000, IndicatorUnit.USD),
    },
    "PY": {
        IndicatorType.PIB: (42_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (4.2, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (6.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (1.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (36.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (5600, IndicatorUnit.USD),
    },
    "PA": {
        IndicatorType.PIB: (76_000_000_000, IndicatorUnit.USD),
        IndicatorType.INFLACION: (1.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.DESEMPLEO: (7.8, IndicatorUnit.PORCENTAJE),
        IndicatorType.BALANZA_COMERCIAL: (-3.5, IndicatorUnit.PORCENTAJE),
        IndicatorType.DEUDA_PIB: (58.0, IndicatorUnit.PORCENTAJE),
        IndicatorType.PIB_PERCAPITA: (17000, IndicatorUnit.USD),
    },
}

USERS = [
    {
        "email": "admin@datapulse.com",
        "nombre_completo": "Admin DataPulse",
        "rol": Rol.ADMIN,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "analista@datapulse.com",
        "nombre_completo": "Analista DataPulse",
        "rol": Rol.ANALISTA,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "viewer@datapulse.com",
        "nombre_completo": "Viewer DataPulse",
        "rol": Rol.VIEWER,
        "is_staff": False,
        "is_superuser": False,
    },
]


class Command(BaseCommand):
    """Load categorized baseline data required by the technical test."""

    help = (
        "Carga datos semilla de la prueba técnica: usuarios, países, indicadores, "
        "tipos de cambio, IRPC, portafolios y alertas de ejemplo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Elimina datos de dominio semilla antes de volver a cargarlos.",
        )

    def handle(self, *args, **options):
        started = timezone.now()
        self._section("SEED DATAPULSE - Inicio")
        self.stdout.write(f"Fecha/hora: {started:%Y-%m-%d %H:%M:%S %Z}")
        self.stdout.write("Fuente: datos estáticos alineados al PDF (sin APIs externas).")

        with transaction.atomic():
            if options["flush"]:
                self._flush_domain_data()

            users = self._seed_users()
            countries = self._seed_countries()
            indicators_count = self._seed_indicators(countries)
            fx_count = self._seed_exchange_rates(countries)
            risk_count = self._seed_risk_indexes(countries)
            portfolios_count, positions_count = self._seed_portfolios(users, countries)
            alerts_count = self._seed_sample_alerts(users, countries)

        self._section("RESUMEN FINAL")
        self.stdout.write(f"  Usuarios:              {len(users)}")
        self.stdout.write(f"  Países:                {len(countries)}")
        self.stdout.write(f"  Indicadores:           {indicators_count}")
        self.stdout.write(f"  Tipos de cambio:       {fx_count}")
        self.stdout.write(f"  Índices de riesgo:     {risk_count}")
        self.stdout.write(f"  Portafolios:           {portfolios_count}")
        self.stdout.write(f"  Posiciones:            {positions_count}")
        self.stdout.write(f"  Alertas de ejemplo:    {alerts_count}")
        elapsed = (timezone.now() - started).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"\nSeed completado en {elapsed:.2f}s."))
        self.stdout.write(self.style.WARNING("Credenciales de prueba (PDF):"))
        for user in users:
            self.stdout.write(f"  - {user.email} / {SEED_PASSWORD} ({user.rol})")

    def _section(self, title: str):
        """Print a visible category header in the terminal."""
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))
        self.stdout.write(self.style.MIGRATE_HEADING(f" {title}"))
        self.stdout.write(self.style.MIGRATE_HEADING("=" * 72))

    def _step(self, message: str):
        """Print a progress step line."""
        self.stdout.write(f"  -> {message}")

    def _ok(self, message: str):
        """Print a success line."""
        self.stdout.write(self.style.SUCCESS(f"  [OK] {message}"))

    def _flush_domain_data(self):
        """Remove seedable domain rows while keeping auth migrations intact."""
        self._section("1) LIMPIEZA (--flush)")
        counts = {
            "Alert": Alert.objects.all().delete()[0],
            "Position": Position.objects.all().delete()[0],
            "Portfolio": Portfolio.objects.all().delete()[0],
            "RiskIndex": RiskIndex.objects.all().delete()[0],
            "ExchangeRate": ExchangeRate.objects.all().delete()[0],
            "EconomicIndicator": EconomicIndicator.objects.all().delete()[0],
            "Country": Country.objects.all().delete()[0],
        }
        deleted_users = User.objects.filter(email__in=[u["email"] for u in USERS]).delete()[0]
        counts["User(seed)"] = deleted_users
        for name, total in counts.items():
            self._step(f"Eliminados {total} registro(s) de {name}")
        self._ok("Limpieza finalizada")

    def _seed_users(self) -> list[User]:
        """Create or update the three technical-test users."""
        self._section("2) USUARIOS DE PRUEBA")
        created_users: list[User] = []
        total = len(USERS)
        for index, payload in enumerate(USERS, start=1):
            self._step(f"[{index}/{total}] Procesando {payload['email']} ({payload['rol']})")
            user, created = User.objects.update_or_create(
                email=payload["email"],
                defaults={
                    "nombre_completo": payload["nombre_completo"],
                    "rol": payload["rol"],
                    "activo": True,
                    "is_staff": payload["is_staff"],
                    "is_superuser": payload["is_superuser"],
                },
            )
            user.set_password(SEED_PASSWORD)
            user.save()
            created_users.append(user)
            action = "creado" if created else "actualizado"
            self._ok(f"Usuario {user.email} {action}")
        return created_users

    def _seed_countries(self) -> list[Country]:
        """Create or update the 10 LatAm countries from the PDF table."""
        self._section("3) PAÍSES (10 — tabla PDF)")
        countries: list[Country] = []
        total = len(COUNTRIES)
        for index, payload in enumerate(COUNTRIES, start=1):
            self._step(
                f"[{index}/{total}] {payload['codigo_iso']} — {payload['nombre']} "
                f"({payload['region']}, {payload['moneda_codigo']})"
            )
            country, created = Country.objects.update_or_create(
                codigo_iso=payload["codigo_iso"],
                defaults={
                    "nombre": payload["nombre"],
                    "moneda_codigo": payload["moneda_codigo"],
                    "moneda_nombre": payload["moneda_nombre"],
                    "region": payload["region"],
                    "latitud": Decimal(payload["latitud"]),
                    "longitud": Decimal(payload["longitud"]),
                    "poblacion": payload["poblacion"],
                    "activo": True,
                },
            )
            countries.append(country)
            action = "creado" if created else "actualizado"
            self._ok(f"{country.codigo_iso} {action}")
        return countries

    def _seed_indicators(self, countries: list[Country]) -> int:
        """Load at least 3 years of indicators per country and type."""
        self._section("4) INDICADORES ECONÓMICOS (≥3 años × 6 tipos × 10 países)")
        total_ops = len(countries) * len(YEARS) * len(IndicatorType)
        done = 0
        created_count = 0

        for country in countries:
            base = INDICATOR_BASE[country.codigo_iso]
            self._step(f"País {country.codigo_iso}: generando indicadores {YEARS[0]}-{YEARS[-1]}")
            for year_index, anio in enumerate(YEARS):
                growth = 1 + (0.02 * year_index)
                for tipo, (valor_base, unidad) in base.items():
                    valor = Decimal(str(round(float(valor_base) * growth, 4)))
                    _, created = EconomicIndicator.objects.update_or_create(
                        pais=country,
                        tipo=tipo,
                        anio=anio,
                        defaults={
                            "valor": valor,
                            "unidad": unidad,
                            "fuente": IndicatorSource.MANUAL,
                        },
                    )
                    done += 1
                    created_count += int(created)
                    if done % 30 == 0 or done == total_ops:
                        pct = (done / total_ops) * 100
                        self.stdout.write(f"     progreso indicadores: {done}/{total_ops} ({pct:.0f}%)")
        self._ok(f"Indicadores listos ({created_count} nuevos, {done} totales procesados)")
        return EconomicIndicator.objects.count()

    def _seed_exchange_rates(self, countries: list[Country]) -> int:
        """Load 30 days of FX history with daily variation."""
        self._section("5) TIPOS DE CAMBIO (30 días históricos)")
        today = date.today()
        total_ops = len(countries) * FX_DAYS
        done = 0
        created_count = 0

        for country in countries:
            meta = next(item for item in COUNTRIES if item["codigo_iso"] == country.codigo_iso)
            base = meta["fx_base"]
            self._step(f"País {country.codigo_iso}: {FX_DAYS} días para {country.moneda_codigo}/USD")
            previous_rate = None
            for day_offset in range(FX_DAYS - 1, -1, -1):
                fecha = today - timedelta(days=day_offset)
                noise = Decimal(str(round(1 + RNG.uniform(-0.01, 0.01), 6)))
                tasa = (base * noise).quantize(Decimal("0.00000001"))
                if previous_rate and previous_rate != 0:
                    variacion = ((tasa - previous_rate) / previous_rate * Decimal("100")).quantize(
                        Decimal("0.0001")
                    )
                else:
                    variacion = Decimal("0.0000")

                existing = ExchangeRate.objects.filter(
                    moneda_origen=country,
                    moneda_destino="USD",
                    fecha=fecha,
                ).first()
                if existing:
                    existing.tasa = tasa
                    existing.variacion_porcentual = variacion
                    existing.fuente = "SEED"
                    existing.save(
                        update_fields=["tasa", "variacion_porcentual", "fuente"]
                    )
                    created = False
                else:
                    ExchangeRate.objects.create(
                        moneda_origen=country,
                        moneda_destino="USD",
                        fecha=fecha,
                        tasa=tasa,
                        variacion_porcentual=variacion,
                        fuente="SEED",
                    )
                    created = True
                previous_rate = tasa
                done += 1
                created_count += int(created)
                if done % 50 == 0 or done == total_ops:
                    pct = (done / total_ops) * 100
                    self.stdout.write(f"     progreso FX: {done}/{total_ops} ({pct:.0f}%)")

        self._ok(f"Tipos de cambio listos ({created_count} nuevos, {done} totales procesados)")
        return ExchangeRate.objects.count()

    def _seed_risk_indexes(self, countries: list[Country]) -> int:
        """Calculate and store IRPC for every country."""
        self._section("6) ÍNDICE DE RIESGO (IRPC) — fórmula PDF")
        # Keep history clean for seed runs: remove previous seed snapshots.
        deleted = RiskIndex.objects.all().delete()[0]
        if deleted:
            self._step(f"Se eliminaron {deleted} índices previos para recalcular")

        total = len(countries)
        for index, country in enumerate(countries, start=1):
            self._step(f"[{index}/{total}] Calculando IRPC para {country.codigo_iso}")
            risk = guardar_irpc(country)
            self._ok(
                f"{country.codigo_iso}: IRPC={risk.indice_compuesto} "
                f"nivel={risk.nivel_riesgo}"
            )
        return RiskIndex.objects.count()

    def _seed_portfolios(self, users: list[User], countries: list[Country]) -> tuple[int, int]:
        """Create two sample portfolios with positions for the analyst user."""
        self._section("7) PORTAFOLIOS Y POSICIONES (2 ejemplos)")
        analista = next(user for user in users if user.rol == Rol.ANALISTA)
        by_iso = {country.codigo_iso: country for country in countries}

        specs = [
            {
                "nombre": "LatAm Crecimiento",
                "descripcion": "Portafolio de ejemplo orientado a mercados andinos y México.",
                "es_publico": True,
                "posiciones": [
                    ("CO", AssetType.RENTA_VARIABLE, "250000.00", date(2024, 1, 15)),
                    ("MX", AssetType.RENTA_FIJA, "180000.00", date(2024, 3, 1)),
                    ("PE", AssetType.COMMODITIES, "90000.00", date(2024, 6, 10)),
                ],
            },
            {
                "nombre": "Cono Sur Conservador",
                "descripcion": "Portafolio privado de ejemplo con exposición al Cono Sur.",
                "es_publico": False,
                "posiciones": [
                    ("CL", AssetType.RENTA_FIJA, "220000.00", date(2023, 11, 20)),
                    ("UY", AssetType.RENTA_VARIABLE, "110000.00", date(2024, 2, 5)),
                    ("BR", AssetType.MONEDA, "75000.00", date(2024, 4, 18)),
                ],
            },
        ]

        portfolios_created = 0
        positions_created = 0
        for index, spec in enumerate(specs, start=1):
            self._step(f"[{index}/{len(specs)}] Portafolio '{spec['nombre']}'")
            portfolio, created = Portfolio.objects.update_or_create(
                usuario=analista,
                nombre=spec["nombre"],
                defaults={
                    "descripcion": spec["descripcion"],
                    "activo": True,
                    "es_publico": spec["es_publico"],
                },
            )
            portfolios_created += int(created)
            self._ok(
                f"Portafolio {portfolio.nombre} "
                f"({'creado' if created else 'actualizado'}, público={portfolio.es_publico})"
            )

            Position.objects.filter(portafolio=portfolio).delete()
            for pais_iso, tipo_activo, monto, fecha_entrada in spec["posiciones"]:
                Position.objects.create(
                    portafolio=portfolio,
                    pais=by_iso[pais_iso],
                    tipo_activo=tipo_activo,
                    monto_inversion_usd=Decimal(monto),
                    fecha_entrada=fecha_entrada,
                    notas="Posición de ejemplo (seed)",
                )
                positions_created += 1
                self._step(
                    f"    + posición {pais_iso}/{tipo_activo} por USD {monto}"
                )

        return Portfolio.objects.count(), Position.objects.count()

    def _seed_sample_alerts(self, users: list[User], countries: list[Country]) -> int:
        """Create a few sample alerts so the alerts module is not empty."""
        self._section("8) ALERTAS DE EJEMPLO")
        analista = next(user for user in users if user.rol == Rol.ANALISTA)
        co = next(country for country in countries if country.codigo_iso == "CO")
        ar = next(country for country in countries if country.codigo_iso == "AR")

        samples = [
            {
                "usuario": None,
                "pais": ar,
                "tipo_alerta": AlertType.INDICADOR,
                "severidad": AlertSeverity.CRITICAL,
                "titulo": "Inflación elevada en Argentina",
                "mensaje": "La inflación supera umbrales críticos según datos seed.",
            },
            {
                "usuario": analista,
                "pais": co,
                "tipo_alerta": AlertType.RIESGO,
                "severidad": AlertSeverity.WARNING,
                "titulo": "Monitorear riesgo de Colombia",
                "mensaje": "Alerta de ejemplo asociada al analista de prueba.",
            },
            {
                "usuario": None,
                "pais": co,
                "tipo_alerta": AlertType.INDICADOR,
                "severidad": AlertSeverity.INFO,
                "titulo": "Datos económicos actualizados (seed)",
                "mensaje": "Se cargaron indicadores semilla para los 10 países.",
            },
        ]

        # Avoid duplicating sample alerts on repeated runs.
        Alert.objects.filter(titulo__in=[item["titulo"] for item in samples]).delete()
        for index, payload in enumerate(samples, start=1):
            self._step(f"[{index}/{len(samples)}] {payload['titulo']}")
            Alert.objects.create(**payload, leida=False)
            self._ok("Alerta creada")
        return Alert.objects.count()
