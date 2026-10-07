from uuid import UUID

from conftest import sample_payload
from sqlalchemy import select

from app.core.enums import JobStatus, RecipientStatus
from app.db.models.job import Job
from app.db.models.recipient import Recipient


def test_create_generation_job(client, db_session, fake_queue) -> None:
    response = client.post("/api/v1/jobs", json=sample_payload())

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == JobStatus.QUEUED
    assert body["total_recipients"] == 1
    assert body["valid_recipients"] == 1
    assert body["invalid_recipients"] == 0
    assert body["status_url"].startswith("/api/v1/jobs/")

    job = db_session.get(Job, UUID(body["job_id"]))
    assert job is not None
    assert job.status == JobStatus.QUEUED
    recipients = db_session.scalars(select(Recipient).where(Recipient.job_id == job.id)).all()
    assert len(recipients) == 1
    assert recipients[0].status == RecipientStatus.PENDING
    assert fake_queue.enqueued == [job.id]
