from pathlib import Path
from uuid import UUID

from conftest import sample_payload

from app.core.enums import RecipientStatus
from app.db.models.recipient import Recipient
from app.services.storage_service import LocalFileStorage
from app.workers.tasks import process_generation_job_logic


def test_generated_certificate_can_be_downloaded(
    client, db_session, session_factory, settings
) -> None:
    response = client.post("/api/v1/jobs", json=sample_payload())
    job_id = UUID(response.json()["job_id"])

    process_generation_job_logic(
        job_id,
        session_factory=session_factory,
        settings=settings,
        storage=LocalFileStorage(settings.storage_path),
    )

    db_session.expire_all()
    recipient = db_session.query(Recipient).filter(Recipient.job_id == job_id).one()
    assert recipient.status == RecipientStatus.SUCCESS
    assert recipient.certificate_path
    assert (Path(settings.storage_path) / recipient.certificate_path).is_file()

    download = client.get(f"/api/v1/jobs/{job_id}/recipients/{recipient.id}/certificate")

    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
    assert len(download.content) > 0
