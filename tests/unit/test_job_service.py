from datetime import UTC, datetime

from app.core.enums import JobStatus, RecipientStatus
from app.db.models.job import Job
from app.db.models.recipient import Recipient
from app.services.job_service import finalize_job_status, recalculate_job_counts


def test_recalculate_job_counts(db_session) -> None:
    job = Job(
        organization_name="ABC",
        certificate_title="Certificate",
        event_name="Workshop",
        issue_date=datetime.now(UTC).date(),
        total_recipients=3,
        valid_recipients=3,
    )
    db_session.add(job)
    db_session.flush()
    db_session.add_all(
        [
            Recipient(
                job_id=job.id, full_name="Alice", course_name="AI", status=RecipientStatus.SUCCESS
            ),
            Recipient(
                job_id=job.id, full_name="Bob", course_name="AI", status=RecipientStatus.FAILED
            ),
            Recipient(
                job_id=job.id, full_name=None, course_name=None, status=RecipientStatus.INVALID
            ),
        ]
    )
    db_session.commit()

    recalculate_job_counts(db_session, job.id)

    assert job.success_count == 1
    assert job.failure_count == 1
    assert job.invalid_recipients == 1
    assert job.valid_recipients == 2


def test_finalize_job_status_with_errors() -> None:
    job = Job(
        organization_name="ABC",
        certificate_title="Certificate",
        event_name="Workshop",
        issue_date=datetime.now(UTC).date(),
        total_recipients=3,
        valid_recipients=2,
        invalid_recipients=1,
        success_count=2,
        failure_count=0,
    )

    finalize_job_status(job)

    assert job.status == JobStatus.COMPLETED_WITH_ERRORS
