"""URL routes for IRPC risk endpoints."""

from django.urls import path

from apps.countries.views_risk import (
    RiskCountryDetailView,
    RiskHistoryView,
    RiskRankingView,
    RiskRecalculateView,
)

urlpatterns = [
    path("", RiskRankingView.as_view(), name="risk-ranking"),
    path("calcular/", RiskRecalculateView.as_view(), name="risk-recalculate"),
    path("<str:codigo_iso>/", RiskCountryDetailView.as_view(), name="risk-detail"),
    path(
        "<str:codigo_iso>/historico/",
        RiskHistoryView.as_view(),
        name="risk-history",
    ),
]
