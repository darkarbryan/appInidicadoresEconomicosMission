"""URL routes for country-related API endpoints."""

from django.urls import path

from apps.countries.views import (
    CountryDetailView,
    CountryExchangeRateView,
    CountryIndicatorsView,
    CountryListView,
    SyncExchangeRatesView,
    SyncIndicatorsView,
)

urlpatterns = [
    path("", CountryListView.as_view(), name="country-list"),
    path("sync-indicadores/", SyncIndicatorsView.as_view(), name="country-sync-indicators"),
    path("sync-tipos-cambio/", SyncExchangeRatesView.as_view(), name="country-sync-fx"),
    path("<str:codigo_iso>/", CountryDetailView.as_view(), name="country-detail"),
    path(
        "<str:codigo_iso>/indicadores/",
        CountryIndicatorsView.as_view(),
        name="country-indicators",
    ),
    path(
        "<str:codigo_iso>/tipo-cambio/",
        CountryExchangeRateView.as_view(),
        name="country-exchange-rate",
    ),
]
