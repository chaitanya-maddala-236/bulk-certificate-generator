from uuid import UUID

from conftest import sample_payload

from app.core.enums import RecipientStatus
from app.db.models.job import Job
from app.db.models.recipient import Recipient


def test_job_status_progress(client, db_session) -> None:
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(
            [
                {"full_name": "Alice", "email": None, "course_name": "AI"},
                {"full_name": "Bob", "email": None, "course_name": "AI"},
                {"full_name": "", "email": "bad", "course_name": ""},
            ]
        ),
    )
    job_id = UUID(response.json()["job_id"])

    job = db_session.get(Job, job_id)
    recipients = db_session.query(Recipient).filter(Recipient.job_id == job.id).all()
    recipients[0].status = RecipientStatus.SUCCESS
    recipients[1].status = RecipientStatus.FAILED
    job.success_count = 1
    job.failure_count = 1
    db_session.commit()

    status = client.get(f"/api/v1/jobs/{job_id}").json()

    assert status["processed_count"] == 3
    assert status["success_count"] == 1
    assert status["failure_count"] == 1
    assert status["invalid_recipients"] == 1
    assert status["progress_percent"] == 100.0
