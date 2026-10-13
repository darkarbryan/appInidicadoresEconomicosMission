from django.apps import AppConfig


class PortfoliosConfig(AppConfig):
    """Django application configuration for investment portfolios."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.portfolios"
    label = "portfolios"
    verbose_name = "Portfolios"
