from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RecipientStatus


class RecipientSubmission(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, examples=["Alice Johnson"])
    email: str | None = Field(default=None, examples=["alice@example.com"])
    course_name: str | None = Field(default=None, examples=["Generative AI"])
    external_id: str | None = Field(default=None, examples=["STU-001"])


class RecipientSummary(BaseModel):
    recipient_id: UUID
    full_name: str | None
    email: str | None
    course_name: str | None
    external_id: str | None
    status: RecipientStatus
    validation_errors: list[str] | None
    error_message: str | None
    certificate_number: str | None
    certificate_filename: str | None
    certificate_size_bytes: int | None
    completed_at: datetime | None


class RecipientListResponse(BaseModel):
    items: list[RecipientSummary]
    page: int
    page_size: int
    total: int
