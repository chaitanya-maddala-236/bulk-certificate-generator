from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class CertificateData:
    organization_name: str
    certificate_title: str
    event_name: str
    issue_date: date
    full_name: str
    course_name: str
    recipient_id: UUID
    certificate_number: str


@dataclass(frozen=True)
class GeneratedCertificate:
    content: bytes
    content_type: str = "application/pdf"


class CertificateGenerator(Protocol):
    def generate(self, data: CertificateData) -> GeneratedCertificate: ...
