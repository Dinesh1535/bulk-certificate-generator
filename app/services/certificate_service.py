import os
from pathlib import Path
from datetime import date
from typing import Optional, Dict, Any
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Rect, Polygon, String, Group
from reportlab.lib.units import inch


class CertificateGenerator:
    """Generates high-resolution vector PDF certificates based on a professional template."""

    def __init__(self):
        # Landscape letter dimensions (11 x 8.5 inches in points: 792 x 612)
        self.width, self.height = landscape(letter)

    def generate_pdf(
        self,
        output_path: Path,
        recipient_name: str,
        event_name: str,
        issuer_name: str,
        certificate_code: str,
        issue_date: date,
        title: str = "Certificate of Completion",
        description: Optional[str] = None,
        custom_attributes: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Renders and saves a certificate PDF to output_path.
        Raises an exception if generation fails or if simulated error is requested.
        """
        # Testing hook to simulate generation failure for specific recipient
        if "__FAIL_SIMULATION__" in recipient_name:
            raise RuntimeError(f"Simulated generation failure for recipient: {recipient_name}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(output_path), pagesize=landscape(letter))
        c.setTitle(f"{title} - {recipient_name}")
        c.setAuthor(issuer_name)
        c.setSubject(event_name)

        w = self.width
        h = self.height

        # 1. Background tint (Subtle warm off-white / ivory)
        c.setFillColor(colors.HexColor("#FDFCF7"))
        c.rect(0, 0, w, h, fill=1, stroke=0)

        # 2. Outer decorative border (Deep Navy / Charcoal)
        margin = 28
        c.setStrokeColor(colors.HexColor("#0F172A"))  # Slate 900
        c.setLineWidth(4)
        c.rect(margin, margin, w - 2 * margin, h - 2 * margin)

        # 3. Inner decorative border (Metallic Warm Gold)
        inner_margin = 35
        c.setStrokeColor(colors.HexColor("#D97706"))  # Amber 600
        c.setLineWidth(1.5)
        c.rect(inner_margin, inner_margin, w - 2 * inner_margin, h - 2 * inner_margin)

        # 4. Corner decorative squares / accents
        corner_size = 14
        c.setFillColor(colors.HexColor("#B45309"))
        for cx in [inner_margin, w - inner_margin]:
            for cy in [inner_margin, h - inner_margin]:
                c.rect(cx - corner_size / 2, cy - corner_size / 2, corner_size, corner_size, fill=1, stroke=0)

        # 5. Header / Issuer organization
        c.setFillColor(colors.HexColor("#475569"))  # Slate 600
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(w / 2, h - 75, issuer_name.upper())

        # 6. Title
        c.setFillColor(colors.HexColor("#0F172A"))  # Slate 900
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(w / 2, h - 118, title.upper())

        # Decorative line below title
        c.setStrokeColor(colors.HexColor("#D97706"))
        c.setLineWidth(2)
        c.line(w / 2 - 120, h - 130, w / 2 + 120, h - 130)

        # 7. Subtitle
        c.setFillColor(colors.HexColor("#64748B"))  # Slate 500
        c.setFont("Helvetica", 13)
        c.drawCentredString(w / 2, h - 165, "THIS IS PROUDLY PRESENTED TO")

        # 8. Recipient Name (Prominent & Elegant)
        c.setFillColor(colors.HexColor("#1E3A8A"))  # Blue 900
        # Dynamic font sizing for long names
        name_len = len(recipient_name)
        font_size = 36 if name_len <= 24 else (28 if name_len <= 36 else 22)
        c.setFont("Times-BoldItalic", font_size)
        c.drawCentredString(w / 2, h - 225, recipient_name)

        # Underline for name with small center diamond
        c.setStrokeColor(colors.HexColor("#CBD5E1"))
        c.setLineWidth(1)
        c.line(w / 2 - 190, h - 240, w / 2 + 190, h - 240)

        # 9. Commendation / Achievement Text
        c.setFillColor(colors.HexColor("#334155"))
        c.setFont("Helvetica", 13)
        c.drawCentredString(
            w / 2,
            h - 275,
            "for successfully completing and demonstrating exceptional achievement in"
        )

        # 10. Event / Course Name
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w / 2, h - 310, event_name)

        # 11. Custom Attributes or Description
        desc_y = h - 340
        if description:
            c.setFillColor(colors.HexColor("#475569"))
            c.setFont("Helvetica-Oblique", 11)
            c.drawCentredString(w / 2, desc_y, description[:110])
            desc_y -= 20

        if custom_attributes:
            attrs_str = " | ".join(f"{k.capitalize()}: {v}" for k, v in custom_attributes.items() if v)
            if attrs_str:
                c.setFillColor(colors.HexColor("#64748B"))
                c.setFont("Helvetica", 10)
                c.drawCentredString(w / 2, desc_y, f"Special Recognition: {attrs_str}")

        # 12. Gold Seal Badge in Center-Bottom
        self._draw_gold_seal(c, w / 2, 135)

        # 13. Left Column: Date & Verification ID
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(75, 150, "DATE ISSUED")
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica", 12)
        formatted_date = issue_date.strftime("%B %d, %Y") if hasattr(issue_date, "strftime") else str(issue_date)
        c.drawString(75, 133, formatted_date)

        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(75, 105, "CREDENTIAL ID")
        c.setFillColor(colors.HexColor("#2563EB"))
        c.setFont("Courier-Bold", 11)
        c.drawString(75, 90, certificate_code)

        # 14. Right Column: Signature Block
        sig_x = w - 240
        c.setStrokeColor(colors.HexColor("#94A3B8"))
        c.setLineWidth(1)
        c.line(sig_x, 130, sig_x + 165, 130)

        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(sig_x + 82, 112, issuer_name)

        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica", 9)
        c.drawCentredString(sig_x + 82, 98, "AUTHORIZED SIGNATURE")

        # Save and finalize page
        c.showPage()
        c.save()

        return output_path

    def _draw_gold_seal(self, c: canvas.Canvas, cx: float, cy: float) -> None:
        """Draws a vector gold seal emblem."""
        # Outer scalloped effect / circle
        c.setFillColor(colors.HexColor("#F59E0B"))  # Gold/Amber 500
        c.circle(cx, cy, 34, fill=1, stroke=0)

        # Inner ring
        c.setFillColor(colors.HexColor("#D97706"))  # Amber 600
        c.circle(cx, cy, 30, fill=1, stroke=0)

        # Inner core
        c.setFillColor(colors.HexColor("#FDE68A"))  # Amber 200
        c.circle(cx, cy, 26, fill=1, stroke=0)

        # Star / text in seal
        c.setFillColor(colors.HexColor("#92400E"))  # Amber 800
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(cx, cy + 4, "OFFICIAL")
        c.drawCentredString(cx, cy - 6, "SEAL")


certificate_generator = CertificateGenerator()
