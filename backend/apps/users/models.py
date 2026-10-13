from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Rol(models.TextChoices):
    """Available user roles for the platform."""

    ADMIN = "ADMIN", "Admin"
    ANALISTA = "ANALISTA", "Analista"
    VIEWER = "VIEWER", "Viewer"


class UserManager(BaseUserManager):
    """Manager that authenticates users by email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and persist a regular user with the given email and password."""
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        extra_fields.setdefault("rol", Rol.ANALISTA)
        extra_fields.setdefault("activo", True)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and persist a superuser with admin privileges."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", Rol.ADMIN)
        extra_fields.setdefault("activo", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model authenticated by email.

    Django entity name is English (User). Domain table and Spanish fields
    follow the technical test vocabulary (usuarios, nombre_completo, etc.).
    """

    username = None
    email = models.EmailField("email", unique=True)
    nombre_completo = models.CharField("nombre completo", max_length=255)
    rol = models.CharField(
        "rol",
        max_length=20,
        choices=Rol.choices,
        default=Rol.ANALISTA,
    )
    fecha_creacion = models.DateTimeField("fecha de creación", auto_now_add=True)
    activo = models.BooleanField("activo", default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre_completo"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Keep Django is_active synchronized with the domain activo flag."""
        self.is_active = self.activo
        super().save(*args, **kwargs)
