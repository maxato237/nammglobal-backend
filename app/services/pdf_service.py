"""Génération de PDFs pour devis et attestations via ReportLab."""
from io import BytesIO


class PDFService:
    @staticmethod
    def generate_quotation_pdf(quotation) -> bytes:
        """Génère le PDF d'un devis. Nécessite reportlab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("NAMM GLOBAL", styles["Title"]))
            story.append(Paragraph(f"Devis N° {quotation.quotation_number}", styles["Heading2"]))
            story.append(Spacer(1, 12))

            items = quotation.items.all() if hasattr(quotation, "items") else []
            if items:
                data = [["Produit", "Qté", "Prix unitaire (FCFA)", "Sous-total"]]
                for item in items:
                    data.append([
                        item.product_name,
                        str(item.quantity),
                        f"{float(item.unit_cost_fcfa):,.0f}",
                        f"{float(item.subtotal_fcfa):,.0f}",
                    ])
                table = Table(data, colWidths=[200, 50, 120, 100])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(table)

            story.append(Spacer(1, 12))
            story.append(Paragraph(f"Total : {float(quotation.total_amount_fcfa):,.0f} FCFA", styles["Heading3"]))

            doc.build(story)
            return buffer.getvalue()
        except ImportError:
            raise RuntimeError("reportlab est requis pour générer des PDFs. Installez-le : pip install reportlab")

    @staticmethod
    def generate_certificate_pdf(enrollment) -> bytes:
        """Génère l'attestation de formation."""
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            story = [
                Paragraph("NAMM GLOBAL — ATTESTATION DE FORMATION", styles["Title"]),
                Spacer(1, 24),
                Paragraph(f"Décernée à : {enrollment.full_name}", styles["Heading2"]),
                Spacer(1, 12),
                Paragraph("Pour avoir complété avec succès la formation NAMM GLOBAL.", styles["Normal"]),
            ]
            doc.build(story)
            return buffer.getvalue()
        except ImportError:
            raise RuntimeError("reportlab est requis.")
