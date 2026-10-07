from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.api.schemas.jobs import (
    JobCreateRequest,
    JobCreateResponse,
    JobListItem,
    JobListResponse,
    JobStatusResponse,
)
from app.config import Settings
from app.core.enums import JobStatus, RecipientStatus
from app.core.exceptions import JobNotFound, RequestLimitExceeded
from app.db.models.job import Job
from app.db.models.recipient import Recipient
from app.services.queue_service import TaskQueue
from app.utils.validation import validate_recipient_payload


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(
        self,
        request: JobCreateRequest,
        *,
        settings: Settings,
        queue: TaskQueue,
    ) -> JobCreateResponse:
        if len(request.recipients) > settings.max_recipients:
            raise RequestLimitExceeded(
                f"At most {settings.max_recipients} recipients may be submitted in one job.",
                details={"max_recipients": settings.max_recipients},
            )

        job = Job(
            organization_name=request.organization_name.strip(),
            certificate_title=request.certificate_title.strip(),
            event_name=request.event_name.strip(),
            issue_date=request.issue_date,
            status=JobStatus.QUEUED,
            total_recipients=len(request.recipients),
        )

        valid_count = 0
        invalid_count = 0
        recipients: list[Recipient] = []

        for raw_recipient in request.recipients:
            validated = validate_recipient_payload(raw_recipient.model_dump())
            status = RecipientStatus.PENDING if validated.is_valid else RecipientStatus.INVALID
            if validated.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

            recipients.append(
                Recipient(
                    job=job,
                    full_name=validated.full_name,
                    email=validated.email,
                    course_name=validated.course_name,
                    external_id=validated.external_id,
                    status=status,
                    validation_errors=validated.errors or None,
                    completed_at=datetime.now(UTC) if status == RecipientStatus.INVALID else None,
                )
            )

        job.valid_recipients = valid_count
        job.invalid_recipients = invalid_count

        try:
            self.db.add(job)
            self.db.add_all(recipients)
            self.db.commit()
            self.db.refresh(job)
        except Exception:
            self.db.rollback()
            raise

        try:
            queue.enqueue_generation_job(job.id)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = f"Failed to enqueue background job: {exc}"
            job.completed_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(job)

        return JobCreateResponse(
            job_id=job.id,
            status=job.status,
            total_recipients=job.total_recipients,
            valid_recipients=job.valid_recipients,
            invalid_recipients=job.invalid_recipients,
            status_url=f"/api/v1/jobs/{job.id}",
        )

    def get_job_or_raise(self, job_id: UUID) -> Job:
        job = self.db.get(Job, job_id)
        if job is None:
            raise JobNotFound()
        return job

    def get_status(self, job_id: UUID) -> JobStatusResponse:
        job = self.get_job_or_raise(job_id)
        processed = job.success_count + job.failure_count + job.invalid_recipients
        progress = (
            round((processed / job.total_recipients * 100), 2) if job.total_recipients else 0.0
        )
        return JobStatusResponse(
            job_id=job.id,
            organization_name=job.organization_name,
            certificate_title=job.certificate_title,
            event_name=job.event_name,
            issue_date=job.issue_date,
            status=job.status,
            total_recipients=job.total_recipients,
            valid_recipients=job.valid_recipients,
            invalid_recipients=job.invalid_recipients,
            success_count=job.success_count,
            failure_count=job.failure_count,
            processed_count=processed,
            progress_percent=progress,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )

    def list_jobs(
        self,
        *,
        page: int,
        page_size: int,
        status: JobStatus | None = None,
    ) -> JobListResponse:
        query: Select[tuple[Job]] = select(Job).order_by(Job.created_at.desc())
        count_query = select(func.count()).select_from(Job)
        if status:
            query = query.where(Job.status == status)
            count_query = count_query.where(Job.status == status)

        total = self.db.scalar(count_query) or 0
        jobs = self.db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()

        return JobListResponse(
            items=[
                JobListItem(
                    job_id=job.id,
                    organization_name=job.organization_name,
                    certificate_title=job.certificate_title,
                    event_name=job.event_name,
                    issue_date=job.issue_date,
                    status=job.status,
                    total_recipients=job.total_recipients,
                    valid_recipients=job.valid_recipients,
                    invalid_recipients=job.invalid_recipients,
                    success_count=job.success_count,
                    failure_count=job.failure_count,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                )
                for job in jobs
            ],
            page=page,
            page_size=page_size,
            total=total,
        )


def recalculate_job_counts(db: Session, job_id: UUID) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise JobNotFound()

    job.success_count = _count_recipients(db, job_id, RecipientStatus.SUCCESS)
    job.failure_count = _count_recipients(db, job_id, RecipientStatus.FAILED)
    job.invalid_recipients = _count_recipients(db, job_id, RecipientStatus.INVALID)
    job.valid_recipients = job.total_recipients - job.invalid_recipients
    return job


def finalize_job_status(job: Job) -> None:
    job.completed_at = datetime.now(UTC)
    if job.failure_count > 0 or job.invalid_recipients > 0:
        job.status = JobStatus.COMPLETED_WITH_ERRORS
    elif job.valid_recipients > 0 and job.success_count == job.valid_recipients:
        job.status = JobStatus.COMPLETED
    else:
        job.status = JobStatus.COMPLETED_WITH_ERRORS


def _count_recipients(db: Session, job_id: UUID, status: RecipientStatus) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Recipient)
            .where(
                Recipient.job_id == job_id,
                Recipient.status == status,
            )
        )
        or 0
    )
