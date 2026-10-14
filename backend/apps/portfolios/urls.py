"""URL routes for portfolio endpoints."""

from django.urls import path

from apps.portfolios.views import (
    PortfolioDetailView,
    PortfolioExportPdfView,
    PortfolioListCreateView,
    PortfolioSummaryView,
    PositionCreateView,
    PositionDetailView,
)

urlpatterns = [
    path("", PortfolioListCreateView.as_view(), name="portfolio-list-create"),
    path("<int:pk>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path("<int:pk>/posiciones/", PositionCreateView.as_view(), name="portfolio-position-create"),
    path(
        "<int:pk>/posiciones/<int:position_id>/",
        PositionDetailView.as_view(),
        name="portfolio-position-detail",
    ),
    path("<int:pk>/resumen/", PortfolioSummaryView.as_view(), name="portfolio-summary"),
    path("<int:pk>/export/pdf/", PortfolioExportPdfView.as_view(), name="portfolio-export-pdf"),
]
