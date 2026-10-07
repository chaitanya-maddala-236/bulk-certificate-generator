from datetime import date
from uuid import uuid4

from pypdf import PdfReader

from app.services.certificate_service import CertificateData
from app.templates.certificate_template import ReportLabCertificateGenerator


def test_reportlab_certificate_generator_creates_pdf(tmp_path) -> None:
    recipient_id = uuid4()
    data = CertificateData(
        organization_name="ABC Learning",
        certificate_title="Certificate of Completion",
        event_name="Advanced AI Workshop",
        issue_date=date(2026, 10, 7),
        full_name="Alice Johnson",
        course_name="Generative AI",
        recipient_id=recipient_id,
        certificate_number="CERT-2026-ABC12345",
    )

    generated = ReportLabCertificateGenerator().generate(data)
    output = tmp_path / "certificate.pdf"
    output.write_bytes(generated.content)

    assert generated.content.startswith(b"%PDF")
    assert output.stat().st_size > 0
    assert "Alice Johnson".upper() in (PdfReader(str(output)).pages[0].extract_text() or "")
