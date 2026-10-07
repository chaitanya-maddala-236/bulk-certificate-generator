from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.core.exceptions import CertificateGenerationError
from app.services.certificate_service import CertificateData, GeneratedCertificate


class ReportLabCertificateGenerator:
    """Generate the single predefined certificate PDF design."""

    def __init__(self) -> None:
        self.font_regular, self.font_bold = self._register_fonts()

    def generate(self, data: CertificateData) -> GeneratedCertificate:
        try:
            buffer = BytesIO()
            page_width, page_height = landscape(letter)
            pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))

            self._draw_background(pdf, page_width, page_height)
            self._draw_text(pdf, data, page_width, page_height)

            pdf.showPage()
            pdf.save()
            return GeneratedCertificate(content=buffer.getvalue())
        except Exception as exc:
            raise CertificateGenerationError(
                f"ReportLab failed to render certificate: {exc}"
            ) from exc

    def _draw_background(self, pdf: canvas.Canvas, width: float, height: float) -> None:
        pdf.setFillColor(colors.HexColor("#FAFAF7"))
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

        pdf.setStrokeColor(colors.HexColor("#1F2937"))
        pdf.setLineWidth(3)
        pdf.rect(0.45 * inch, 0.45 * inch, width - 0.9 * inch, height - 0.9 * inch, fill=0)

        pdf.setStrokeColor(colors.HexColor("#B08D57"))
        pdf.setLineWidth(1.5)
        pdf.rect(0.62 * inch, 0.62 * inch, width - 1.24 * inch, height - 1.24 * inch, fill=0)

    def _draw_text(
        self,
        pdf: canvas.Canvas,
        data: CertificateData,
        width: float,
        height: float,
    ) -> None:
        center_x = width / 2
        y = height - 1.15 * inch

        self._center(
            pdf, data.organization_name.upper(), center_x, y, 19, self.font_bold, "#111827"
        )
        y -= 0.7 * inch
        self._center(
            pdf, data.certificate_title.upper(), center_x, y, 24, self.font_bold, "#7C2D12"
        )
        y -= 0.6 * inch
        self._center(pdf, "This certifies that", center_x, y, 13, self.font_regular, "#374151")
        y -= 0.56 * inch
        self._center(pdf, data.full_name.upper(), center_x, y, 30, self.font_bold, "#111827")
        y -= 0.52 * inch
        self._center(
            pdf, "has successfully completed", center_x, y, 13, self.font_regular, "#374151"
        )
        y -= 0.45 * inch
        self._center(pdf, data.course_name.upper(), center_x, y, 19, self.font_bold, "#1F2937")
        y -= 0.42 * inch
        self._center(pdf, data.event_name, center_x, y, 14, self.font_regular, "#374151")
        y -= 0.42 * inch
        self._center(
            pdf,
            data.issue_date.strftime("%d %B %Y"),
            center_x,
            y,
            13,
            self.font_regular,
            "#374151",
        )

        signature_y = 1.35 * inch
        left_x = width * 0.32
        right_x = width * 0.68
        pdf.setStrokeColor(colors.HexColor("#374151"))
        pdf.line(left_x - 1.05 * inch, signature_y, left_x + 1.05 * inch, signature_y)
        pdf.line(right_x - 1.05 * inch, signature_y, right_x + 1.05 * inch, signature_y)
        self._center(
            pdf,
            "Instructor",
            left_x,
            signature_y - 0.22 * inch,
            10,
            self.font_regular,
            "#374151",
        )
        self._center(
            pdf,
            "Director",
            right_x,
            signature_y - 0.22 * inch,
            10,
            self.font_regular,
            "#374151",
        )

        self._center(
            pdf,
            f"Certificate ID: {data.certificate_number}",
            center_x,
            0.88 * inch,
            9,
            self.font_regular,
            "#4B5563",
        )

    def _center(
        self,
        pdf: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        size: int,
        font: str,
        color: str,
    ) -> None:
        pdf.setFillColor(colors.HexColor(color))
        pdf.setFont(font, size)
        pdf.drawCentredString(x, y, text)

    def _register_fonts(self) -> tuple[str, str]:
        try:
            import reportlab

            font_dir = reportlab.__path__[0] + "/fonts"
            regular_path = f"{font_dir}/Vera.ttf"
            bold_path = f"{font_dir}/VeraBd.ttf"
            pdfmetrics.registerFont(TTFont("CertificateRegular", regular_path))
            pdfmetrics.registerFont(TTFont("CertificateBold", bold_path))
            return "CertificateRegular", "CertificateBold"
        except Exception:
            return "Helvetica", "Helvetica-Bold"
