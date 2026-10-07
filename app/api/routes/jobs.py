from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_database_session,
    get_settings_dependency,
    get_storage_service,
    get_task_queue,
)
from app.api.schemas.jobs import (
    JobCreateRequest,
    JobCreateResponse,
    JobListResponse,
    JobStatusResponse,
)
from app.api.schemas.recipients import RecipientListResponse, RecipientSummary
from app.config import Settings
from app.core.enums import JobStatus, RecipientStatus
from app.services.job_service import JobService
from app.services.queue_service import TaskQueue
from app.services.recipient_service import RecipientService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a bulk certificate generation job",
)
def create_job(
    request: JobCreateRequest,
    db: Session = Depends(get_database_session),
    settings: Settings = Depends(get_settings_dependency),
    queue: TaskQueue = Depends(get_task_queue),
) -> JobCreateResponse:
    return JobService(db).create_job(request, settings=settings, queue=queue)


@router.get("", response_model=JobListResponse, summary="List generation jobs")
def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_database_session),
) -> JobListResponse:
    return JobService(db).list_jobs(page=page, page_size=page_size, status=status_filter)


@router.get("/{job_id}", response_model=JobStatusResponse, summary="Get job progress and result")
def get_job(job_id: UUID, db: Session = Depends(get_database_session)) -> JobStatusResponse:
    return JobService(db).get_status(job_id)


@router.get(
    "/{job_id}/recipients",
    response_model=RecipientListResponse,
    summary="List recipients for a job",
)
def list_recipients(
    job_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status_filter: RecipientStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_database_session),
) -> RecipientListResponse:
    return RecipientService(db).list_recipients(
        job_id=job_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )


@router.get(
    "/{job_id}/recipients/{recipient_id}",
    response_model=RecipientSummary,
    summary="Get recipient generation details",
)
def get_recipient(
    job_id: UUID,
    recipient_id: UUID,
    db: Session = Depends(get_database_session),
) -> RecipientSummary:
    return RecipientService(db).get_detail(job_id=job_id, recipient_id=recipient_id)


@router.get(
    "/{job_id}/recipients/{recipient_id}/certificate",
    summary="Download a generated recipient certificate PDF",
)
def download_certificate(
    job_id: UUID,
    recipient_id: UUID,
    db: Session = Depends(get_database_session),
    storage: StorageService = Depends(get_storage_service),
) -> FileResponse:
    file_path, filename = RecipientService(db).get_certificate_path(
        job_id=job_id,
        recipient_id=recipient_id,
        storage=storage,
    )
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename or f"{recipient_id}.pdf",
    )
