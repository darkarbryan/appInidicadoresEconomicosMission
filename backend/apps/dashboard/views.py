"""HTTP endpoints for dashboard KPIs, map and trend charts."""

from django.db.models import Avg, OuterRef, Q, Subquery
from django.utils import timezone
from rest_framework import permissions
from rest_framework.views import APIView

from apiMission.responses import error_response, ok_response
from apps.alerts.models import Alert
from apps.countries.models import Country, EconomicIndicator, IndicatorType, RiskIndex
from apps.portfolios.models import Portfolio


RISK_COLORS = {
    "BAJO": "#22c55e",
    "MODERADO": "#eab308",
    "ALTO": "#f97316",
    "CRITICO": "#ef4444",
}


def _latest_risk_per_country():
    """Subquery helper returning the latest RiskIndex id per country."""
    return (
        RiskIndex.objects.filter(pais=OuterRef("pais"))
        .order_by("-fecha_calculo", "-id")
        .values("id")[:1]
    )


class DashboardSummaryView(APIView):
    """Return global KPI cards for the main dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Compute totals for countries, alerts, portfolios and average IRPC."""
        latest_risks = RiskIndex.objects.filter(id=Subquery(_latest_risk_per_country()))
        promedio = latest_risks.aggregate(avg=Avg("indice_compuesto"))["avg"]
        alertas_activas = Alert.objects.filter(
            Q(usuario=request.user) | Q(usuario__isnull=True),
            leida=False,
        ).count()
        portafolios_usuario = Portfolio.objects.filter(
            usuario=request.user,
            activo=True,
        ).count()

        return ok_response(
            {
                "total_paises": Country.objects.filter(activo=True).count(),
                "alertas_activas": alertas_activas,
                "portafolios_usuario": portafolios_usuario,
                "promedio_irpc_region": (
                    round(float(promedio), 2) if promedio is not None else None
                ),
                "fecha": timezone.now().isoformat(),
            }
        )


class DashboardMapView(APIView):
    """Return map-ready country points with IRPC color coding."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Build geo payload for LatAm risk visualization."""
        latest = (
            RiskIndex.objects.filter(id=Subquery(_latest_risk_per_country()))
            .select_related("pais")
            .order_by("pais__nombre")
        )
        puntos = []
        for risk in latest:
            country = risk.pais
            puntos.append(
                {
                    "codigo_iso": country.codigo_iso,
                    "nombre": country.nombre,
                    "latitud": country.latitud,
                    "longitud": country.longitud,
                    "indice_compuesto": risk.indice_compuesto,
                    "nivel_riesgo": risk.nivel_riesgo,
                    "color": RISK_COLORS.get(risk.nivel_riesgo, "#94a3b8"),
                }
            )
        return ok_response({"paises": puntos})


class DashboardTrendsView(APIView):
    """Return multi-year indicator series for chart comparisons."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Build trend series for up to 3 countries and one indicator type.

        Query params:
        - indicador: IndicatorType value (default PIB)
        - paises: comma-separated ISO codes (max 3). Defaults to CO,BR,MX.
        - anios: number of years (default 5, max 10)
        """
        tipo = (request.query_params.get("indicador") or IndicatorType.PIB).upper()
        if tipo not in IndicatorType.values:
            return error_response(
                {"detail": f"Indicador inválido. Valores: {', '.join(IndicatorType.values)}"}
            )

        raw_paises = request.query_params.get("paises", "CO,BR,MX")
        codigos = [code.strip().upper() for code in raw_paises.split(",") if code.strip()]
        if not codigos or len(codigos) > 3:
            return error_response({"detail": "Debes indicar entre 1 y 3 códigos de país."})

        try:
            anios = int(request.query_params.get("anios", 5))
            if anios < 1 or anios > 10:
                raise ValueError
        except (TypeError, ValueError):
            return error_response({"detail": "El parámetro anios debe ser un entero entre 1 y 10."})

        current_year = timezone.now().year
        year_from = current_year - anios + 1
        series = []
        for codigo in codigos:
            country = Country.objects.filter(codigo_iso=codigo, activo=True).first()
            if not country:
                continue
            rows = (
                EconomicIndicator.objects.filter(
                    pais=country,
                    tipo=tipo,
                    anio__gte=year_from,
                )
                .order_by("anio")
                .values("anio", "valor", "unidad")
            )
            series.append(
                {
                    "codigo_iso": country.codigo_iso,
                    "nombre": country.nombre,
                    "indicador": tipo,
                    "puntos": list(rows),
                }
            )

        return ok_response(
            {
                "indicador": tipo,
                "anio_desde": year_from,
                "anio_hasta": current_year,
                "series": series,
            }
        )
