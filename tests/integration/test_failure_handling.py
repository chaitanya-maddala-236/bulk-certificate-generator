from uuid import UUID

from conftest import sample_payload

from app.core.enums import JobStatus, RecipientStatus
from app.db.models.job import Job
from app.db.models.recipient import Recipient
from app.services.certificate_service import CertificateData, GeneratedCertificate
from app.services.storage_service import LocalFileStorage
from app.workers.tasks import process_generation_job_logic


class FailingForBobGenerator:
    def generate(self, data: CertificateData) -> GeneratedCertificate:
        if data.full_name == "Bob Smith":
            raise RuntimeError("Intentional Bob failure")
        return GeneratedCertificate(content=b"%PDF-1.4\nfake certificate\n%%EOF")


def test_individual_certificate_failure_does_not_stop_job(
    client,
    db_session,
    session_factory,
    settings,
) -> None:
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(
            [
                {"full_name": "Alice Johnson", "email": None, "course_name": "AI"},
                {"full_name": "Bob Smith", "email": None, "course_name": "AI"},
                {"full_name": "Charlie Brown", "email": None, "course_name": "AI"},
            ]
        ),
    )
    job_id = UUID(response.json()["job_id"])

    process_generation_job_logic(
        job_id,
        session_factory=session_factory,
        settings=settings,
        generator=FailingForBobGenerator(),
        storage=LocalFileStorage(settings.storage_path),
    )

    db_session.expire_all()
    job = db_session.get(Job, job_id)
    recipients = {
        recipient.full_name: recipient
        for recipient in db_session.query(Recipient).filter(Recipient.job_id == job_id).all()
    }

    assert job.status == JobStatus.COMPLETED_WITH_ERRORS
    assert job.success_count == 2
    assert job.failure_count == 1
    assert recipients["Alice Johnson"].status == RecipientStatus.SUCCESS
    assert recipients["Bob Smith"].status == RecipientStatus.FAILED
    assert "Intentional Bob failure" in recipients["Bob Smith"].error_message
    assert recipients["Charlie Brown"].status == RecipientStatus.SUCCESS
