from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Django application configuration for the users module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    label = "users"
    verbose_name = "Users"
