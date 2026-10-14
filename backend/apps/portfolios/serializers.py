"""Serializers for portfolios and investment positions."""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from apps.countries.models import RiskIndex
from apps.portfolios.models import AssetType, Portfolio, Position


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for portfolio positions."""

    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)

    class Meta:
        model = Position
        fields = (
            "id",
            "pais",
            "pais_nombre",
            "tipo_activo",
            "monto_inversion_usd",
            "fecha_entrada",
            "fecha_salida",
            "notas",
        )
        read_only_fields = ("id",)


class PositionWriteSerializer(serializers.ModelSerializer):
    """Create/update validations for a portfolio position."""

    class Meta:
        model = Position
        fields = (
            "pais",
            "tipo_activo",
            "monto_inversion_usd",
            "fecha_entrada",
            "fecha_salida",
            "notas",
        )

    def validate_monto_inversion_usd(self, value):
        """Enforce technical-test min/max investment bounds."""
        if value < Decimal("1000"):
            raise serializers.ValidationError("El monto mínimo de inversión es USD 1,000.")
        if value > Decimal("10000000"):
            raise serializers.ValidationError("El monto máximo de inversión es USD 10,000,000.")
        return value

    def validate_fecha_entrada(self, value):
        """Reject future entry dates."""
        if value > date.today():
            raise serializers.ValidationError("La fecha de entrada no puede ser futura.")
        return value

    def validate(self, attrs):
        """Apply cross-field business rules from the technical test."""
        portafolio = self.context["portafolio"]
        instance = getattr(self, "instance", None)
        pais = attrs.get("pais") or (instance.pais if instance else None)
        tipo_activo = attrs.get("tipo_activo") or (instance.tipo_activo if instance else None)
        monto = attrs.get("monto_inversion_usd")
        if monto is None and instance:
            monto = instance.monto_inversion_usd
        fecha_entrada = attrs.get("fecha_entrada") or (instance.fecha_entrada if instance else None)
        fecha_salida = attrs.get("fecha_salida", instance.fecha_salida if instance else None)

        if fecha_salida and fecha_entrada and fecha_salida <= fecha_entrada:
            raise serializers.ValidationError(
                {"fecha_salida": "La fecha de salida debe ser posterior a la fecha de entrada."}
            )

        if pais and tipo_activo == AssetType.MONEDA and pais.moneda_codigo == "USD":
            raise serializers.ValidationError(
                {
                    "tipo_activo": (
                        "No se puede agregar una posición de tipo MONEDA "
                        "para un país cuya moneda es USD."
                    )
                }
            )

        activos = Position.objects.filter(portafolio=portafolio, fecha_salida__isnull=True)
        if instance:
            activos = activos.exclude(pk=instance.pk)

        total_actual = activos.aggregate(total=Sum("monto_inversion_usd"))["total"] or Decimal("0")
        nuevo_total = total_actual + (monto or Decimal("0"))
        if nuevo_total > Decimal("50000000"):
            raise serializers.ValidationError(
                {
                    "monto_inversion_usd": (
                        "El monto total del portafolio no puede superar USD 50,000,000."
                    )
                }
            )

        if pais and tipo_activo and fecha_salida is None:
            same = activos.filter(pais=pais, tipo_activo=tipo_activo).count()
            if same >= 2:
                raise serializers.ValidationError(
                    {
                        "tipo_activo": (
                            "No se pueden tener más de 2 posiciones activas "
                            "del mismo tipo_activo en el mismo país."
                        )
                    }
                )
        return attrs


class PortfolioSerializer(serializers.ModelSerializer):
    """List representation of a portfolio."""

    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)
    total_posiciones = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "nombre",
            "descripcion",
            "usuario",
            "usuario_email",
            "fecha_creacion",
            "fecha_modificacion",
            "activo",
            "es_publico",
            "total_posiciones",
        )
        read_only_fields = (
            "id",
            "usuario",
            "fecha_creacion",
            "fecha_modificacion",
        )

    def get_total_posiciones(self, obj):
        """Count active (open) positions in the portfolio."""
        return obj.posiciones.filter(fecha_salida__isnull=True).count()


class PortfolioDetailSerializer(PortfolioSerializer):
    """Detail representation including positions and simple metrics."""

    posiciones = PositionSerializer(many=True, read_only=True)
    metricas = serializers.SerializerMethodField()

    class Meta(PortfolioSerializer.Meta):
        fields = PortfolioSerializer.Meta.fields + ("posiciones", "metricas")

    def get_metricas(self, obj):
        """Compute invested total and weighted average risk for open positions."""
        abiertas = obj.posiciones.filter(fecha_salida__isnull=True).select_related("pais")
        total = abiertas.aggregate(total=Sum("monto_inversion_usd"))["total"] or Decimal("0")
        riesgo_ponderado = None
        if total > 0:
            acumulado = Decimal("0")
            peso = Decimal("0")
            for position in abiertas:
                risk = (
                    RiskIndex.objects.filter(pais=position.pais)
                    .order_by("-fecha_calculo")
                    .first()
                )
                if risk:
                    acumulado += Decimal(position.monto_inversion_usd) * risk.indice_compuesto
                    peso += Decimal(position.monto_inversion_usd)
            if peso > 0:
                riesgo_ponderado = (acumulado / peso).quantize(Decimal("0.01"))
        return {
            "monto_total_usd": total,
            "riesgo_promedio_ponderado": riesgo_ponderado,
            "posiciones_abiertas": abiertas.count(),
        }


class PortfolioWriteSerializer(serializers.ModelSerializer):
    """Create/update payload for portfolios."""

    class Meta:
        model = Portfolio
        fields = ("nombre", "descripcion", "es_publico", "activo")

    def validate_nombre(self, value):
        """Enforce name length and uniqueness per user."""
        nombre = value.strip()
        if len(nombre) < 3:
            raise serializers.ValidationError("El nombre debe tener al menos 3 caracteres.")
        if len(nombre) > 100:
            raise serializers.ValidationError("El nombre no puede superar 100 caracteres.")
        user = self.context["request"].user
        qs = Portfolio.objects.filter(usuario=user, nombre__iexact=nombre)
        instance = getattr(self, "instance", None)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya tienes un portafolio con este nombre.")
        return nombre

    def validate_descripcion(self, value):
        """Limit description length to 500 characters."""
        if value and len(value) > 500:
            raise serializers.ValidationError("La descripción no puede superar 500 caracteres.")
        return value or ""
