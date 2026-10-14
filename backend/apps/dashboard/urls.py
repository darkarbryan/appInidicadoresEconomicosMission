"""URL routes for dashboard endpoints."""

from django.urls import path

from apps.dashboard.views import DashboardMapView, DashboardSummaryView, DashboardTrendsView

urlpatterns = [
    path("resumen/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("mapa/", DashboardMapView.as_view(), name="dashboard-map"),
    path("tendencias/", DashboardTrendsView.as_view(), name="dashboard-trends"),
]
