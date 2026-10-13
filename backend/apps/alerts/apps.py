from django.apps import AppConfig


class AlertsConfig(AppConfig):
    """Django application configuration for system alerts."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.alerts"
    label = "alerts"
    verbose_name = "Alerts"
