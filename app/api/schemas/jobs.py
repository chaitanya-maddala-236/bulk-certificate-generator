from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.recipients import RecipientSubmission
from app.core.enums import JobStatus


class JobCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    organization_name: str = Field(
        min_length=1,
        max_length=255,
        examples=["ABC Learning"],
        description="Organization shown at the top of each certificate.",
    )
    certificate_title: str = Field(
        min_length=1,
        max_length=255,
        examples=["Certificate of Completion"],
    )
    event_name: str = Field(min_length=1, max_length=255, examples=["Advanced AI Workshop"])
    issue_date: date = Field(examples=["2026-10-07"])
    recipients: list[RecipientSubmission] = Field(min_length=1)


class JobCreateResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    total_recipients: int
    valid_recipients: int
    invalid_recipients: int
    status_url: str


class JobStatusResponse(BaseModel):
    job_id: UUID
    organization_name: str
    certificate_title: str
    event_name: str
    issue_date: date
    status: JobStatus
    total_recipients: int
    valid_recipients: int
    invalid_recipients: int
    success_count: int
    failure_count: int
    processed_count: int
    progress_percent: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class JobListItem(BaseModel):
    job_id: UUID
    organization_name: str
    certificate_title: str
    event_name: str
    issue_date: date
    status: JobStatus
    total_recipients: int
    valid_recipients: int
    invalid_recipients: int
    success_count: int
    failure_count: int
    created_at: datetime
    completed_at: datetime | None


class JobListResponse(BaseModel):
    items: list[JobListItem]
    page: int
    page_size: int
    total: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
