"""URL routes for alert endpoints."""

from django.urls import path

from apps.alerts.views import (
    AlertListView,
    AlertMarkAllReadView,
    AlertMarkReadView,
    AlertSummaryView,
)

urlpatterns = [
    path("", AlertListView.as_view(), name="alert-list"),
    path("resumen/", AlertSummaryView.as_view(), name="alert-summary"),
    path("leer-todas/", AlertMarkAllReadView.as_view(), name="alert-mark-all-read"),
    path("<int:pk>/leer/", AlertMarkReadView.as_view(), name="alert-mark-read"),
]
