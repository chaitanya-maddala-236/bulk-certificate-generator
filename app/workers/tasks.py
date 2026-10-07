import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.core.enums import JobStatus, RecipientStatus
from app.db.models.job import Job
from app.db.models.recipient import Recipient
from app.db.session import SessionLocal
from app.services.certificate_service import CertificateData, CertificateGenerator
from app.services.job_service import finalize_job_status, recalculate_job_counts
from app.services.storage_service import LocalFileStorage, StorageService
from app.templates.certificate_template import ReportLabCertificateGenerator
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_generation_job")
def process_generation_job(job_id: str) -> None:
    process_generation_job_logic(UUID(job_id))


def process_generation_job_logic(
    job_id: UUID | str,
    *,
    session_factory: Callable[[], Session] | sessionmaker[Session] = SessionLocal,
    settings: Settings | None = None,
    generator: CertificateGenerator | None = None,
    storage: StorageService | None = None,
) -> None:
    """Process one generation job while isolating recipient-level failures."""

    job_id = UUID(str(job_id))
    settings = settings or get_settings()
    generator = generator or ReportLabCertificateGenerator()
    storage = storage or LocalFileStorage(settings.storage_path)

    db = session_factory()
    try:
        job = db.get(Job, job_id)
        if job is None:
            logger.warning("Generation job %s was not found; worker is exiting.", job_id)
            return

        if job.status in {
            JobStatus.COMPLETED,
            JobStatus.COMPLETED_WITH_ERRORS,
            JobStatus.FAILED,
        }:
            logger.info("Generation job %s is already final with status %s.", job_id, job.status)
            return

        job.status = JobStatus.RUNNING
        job.started_at = job.started_at or datetime.now(UTC)
        db.commit()

        while True:
            pending_ids = list(
                db.scalars(
                    select(Recipient.id)
                    .where(
                        Recipient.job_id == job_id,
                        Recipient.status == RecipientStatus.PENDING,
                    )
                    .order_by(Recipient.created_at.asc())
                    .limit(settings.process_batch_size)
                )
            )

            if not pending_ids:
                break

            for recipient_id in pending_ids:
                _process_one_recipient(
                    db=db,
                    job_id=job_id,
                    recipient_id=recipient_id,
                    generator=generator,
                    storage=storage,
                )

        job = recalculate_job_counts(db, job_id)
        finalize_job_status(job)
        db.commit()
        logger.info("Generation job %s finished with status %s.", job_id, job.status)
    except Exception as exc:
        db.rollback()
        logger.exception("System-level failure while processing generation job %s.", job_id)
        failed_job = db.get(Job, job_id)
        if failed_job is not None:
            failed_job.status = JobStatus.FAILED
            failed_job.error_message = f"System-level worker failure: {exc}"
            failed_job.completed_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


def _process_one_recipient(
    *,
    db: Session,
    job_id: UUID,
    recipient_id: UUID,
    generator: CertificateGenerator,
    storage: StorageService,
) -> None:
    recipient = db.get(Recipient, recipient_id)
    if recipient is None or recipient.job_id != job_id:
        logger.warning("Recipient %s was not found for job %s.", recipient_id, job_id)
        return

    if recipient.status != RecipientStatus.PENDING:
        logger.info("Recipient %s is %s; skipping.", recipient_id, recipient.status)
        return

    try:
        recipient.status = RecipientStatus.PROCESSING
        db.commit()

        job = db.get(Job, job_id)
        if job is None:
            raise RuntimeError("Job disappeared during recipient processing.")

        if not recipient.full_name or not recipient.course_name:
            raise RuntimeError("Recipient is missing required normalized data.")

        certificate_number = build_certificate_number(job.issue_date.year, recipient.id)
        certificate = generator.generate(
            CertificateData(
                organization_name=job.organization_name,
                certificate_title=job.certificate_title,
                event_name=job.event_name,
                issue_date=job.issue_date,
                full_name=recipient.full_name,
                course_name=recipient.course_name,
                recipient_id=recipient.id,
                certificate_number=certificate_number,
            )
        )
        stored_file = storage.save(job.id, recipient.id, certificate.content)

        recipient.status = RecipientStatus.SUCCESS
        recipient.error_message = None
        recipient.certificate_number = certificate_number
        recipient.certificate_path = stored_file.relative_path
        recipient.certificate_filename = stored_file.filename
        recipient.certificate_size_bytes = stored_file.size_bytes
        recipient.completed_at = datetime.now(UTC)
        recalculate_job_counts(db, job_id)
        db.commit()
        logger.info("Recipient %s certificate generated successfully.", recipient_id)
    except Exception as exc:
        db.rollback()
        failed_recipient = db.get(Recipient, recipient_id)
        if failed_recipient is not None:
            failed_recipient.status = RecipientStatus.FAILED
            failed_recipient.error_message = str(exc)
            failed_recipient.completed_at = datetime.now(UTC)
            recalculate_job_counts(db, job_id)
            db.commit()
        logger.exception("Recipient %s failed during certificate generation.", recipient_id)


def build_certificate_number(issue_year: int, recipient_id: UUID) -> str:
    return f"CERT-{issue_year}-{recipient_id.hex[:8].upper()}"
