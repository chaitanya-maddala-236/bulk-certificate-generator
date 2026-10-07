from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.schemas.recipients import RecipientListResponse, RecipientSummary
from app.core.enums import RecipientStatus
from app.core.exceptions import CertificateNotReady, RecipientNotFound, StorageError
from app.db.models.recipient import Recipient
from app.services.job_service import JobService
from app.services.storage_service import StorageService


class RecipientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_recipients(
        self,
        *,
        job_id: UUID,
        page: int,
        page_size: int,
        status: RecipientStatus | None = None,
    ) -> RecipientListResponse:
        JobService(self.db).get_job_or_raise(job_id)

        query = (
            select(Recipient).where(Recipient.job_id == job_id).order_by(Recipient.created_at.asc())
        )
        count_query = select(func.count()).select_from(Recipient).where(Recipient.job_id == job_id)
        if status:
            query = query.where(Recipient.status == status)
            count_query = count_query.where(Recipient.status == status)

        total = self.db.scalar(count_query) or 0
        recipients = self.db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
        return RecipientListResponse(
            items=[recipient_to_summary(item) for item in recipients],
            page=page,
            page_size=page_size,
            total=total,
        )

    def get_recipient_or_raise(self, *, job_id: UUID, recipient_id: UUID) -> Recipient:
        recipient = self.db.scalar(
            select(Recipient).where(Recipient.id == recipient_id, Recipient.job_id == job_id)
        )
        if recipient is None:
            raise RecipientNotFound()
        return recipient

    def get_detail(self, *, job_id: UUID, recipient_id: UUID) -> RecipientSummary:
        return recipient_to_summary(
            self.get_recipient_or_raise(job_id=job_id, recipient_id=recipient_id)
        )

    def get_certificate_path(
        self,
        *,
        job_id: UUID,
        recipient_id: UUID,
        storage: StorageService,
    ):
        recipient = self.get_recipient_or_raise(job_id=job_id, recipient_id=recipient_id)

        if recipient.status != RecipientStatus.SUCCESS:
            raise CertificateNotReady(
                "Certificate is not available for this recipient.",
                details={
                    "recipient_status": recipient.status,
                    "error_message": recipient.error_message,
                    "validation_errors": recipient.validation_errors,
                },
            )

        if not recipient.certificate_path:
            raise CertificateNotReady("Certificate metadata is missing for this recipient.")

        if not storage.exists(recipient.certificate_path):
            raise StorageError("Certificate file is missing from storage.")

        return storage.resolve(recipient.certificate_path), recipient.certificate_filename


def recipient_to_summary(recipient: Recipient) -> RecipientSummary:
    return RecipientSummary(
        recipient_id=recipient.id,
        full_name=recipient.full_name,
        email=recipient.email,
        course_name=recipient.course_name,
        external_id=recipient.external_id,
        status=recipient.status,
        validation_errors=recipient.validation_errors,
        error_message=recipient.error_message,
        certificate_number=recipient.certificate_number,
        certificate_filename=recipient.certificate_filename,
        certificate_size_bytes=recipient.certificate_size_bytes,
        completed_at=recipient.completed_at,
    )
