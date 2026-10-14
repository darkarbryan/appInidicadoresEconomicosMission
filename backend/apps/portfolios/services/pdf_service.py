"""PDF report generation for investment portfolios."""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.countries.models import RiskIndex
from apps.portfolios.models import Portfolio


def build_portfolio_pdf(portfolio: Portfolio) -> bytes:
    """
    Build a simple PDF report for a portfolio.

    Includes header metadata, open positions table and basic totals.
    """
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("DataPulse Latam - Reporte de Portafolio", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Nombre:</b> {portfolio.nombre}", styles["Normal"]))
    story.append(
        Paragraph(f"<b>Propietario:</b> {portfolio.usuario.email}", styles["Normal"])
    )
    story.append(
        Paragraph(
            f"<b>Publico:</b> {'Si' if portfolio.es_publico else 'No'}",
            styles["Normal"],
        )
    )
    if portfolio.descripcion:
        story.append(Paragraph(f"<b>Descripcion:</b> {portfolio.descripcion}", styles["Normal"]))
    story.append(Spacer(1, 16))

    abiertas = portfolio.posiciones.filter(fecha_salida__isnull=True).select_related("pais")
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
                acumulado += position.monto_inversion_usd * risk.indice_compuesto
                peso += position.monto_inversion_usd
        if peso > 0:
            riesgo_ponderado = (acumulado / peso).quantize(Decimal("0.01"))

    story.append(Paragraph(f"<b>Monto total USD:</b> {total}", styles["Normal"]))
    story.append(
        Paragraph(
            f"<b>Riesgo promedio ponderado:</b> {riesgo_ponderado if riesgo_ponderado is not None else 'N/D'}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 16))
    story.append(Paragraph("Posiciones abiertas", styles["Heading2"]))

    table_data = [["Pais", "Tipo activo", "Monto USD", "Fecha entrada"]]
    for position in abiertas:
        table_data.append(
            [
                position.pais_id,
                position.tipo_activo,
                f"{position.monto_inversion_usd}",
                position.fecha_entrada.isoformat(),
            ]
        )

    if len(table_data) == 1:
        table_data.append(["-", "-", "0", "-"])

    table = Table(table_data, colWidths=[80, 120, 100, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)
    document.build(story)
    return buffer.getvalue()
