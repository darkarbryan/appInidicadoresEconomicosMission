from django.apps import AppConfig


class CountriesConfig(AppConfig):
    """Django application configuration for countries and related indicators."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.countries"
    label = "countries"
    verbose_name = "Countries"
