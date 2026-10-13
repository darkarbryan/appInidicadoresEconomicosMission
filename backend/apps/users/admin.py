from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin configuration for the custom User model."""

    ordering = ("email",)
    list_display = ("email", "nombre_completo", "rol", "activo", "fecha_creacion", "is_staff")
    list_filter = ("rol", "activo", "is_staff")
    search_fields = ("email", "nombre_completo")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("nombre_completo",)}),
        ("Permisos", {"fields": ("rol", "activo", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "fecha_creacion")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nombre_completo", "rol", "password1", "password2", "activo"),
            },
        ),
    )
    readonly_fields = ("fecha_creacion",)
    filter_horizontal = ("groups", "user_permissions")
