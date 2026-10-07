import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecipientStatus
from app.db.base import Base


class Recipient(Base):
    __tablename__ = "recipients"
    __table_args__ = (
        Index("ix_recipients_job_id", "job_id"),
        Index("ix_recipients_job_id_status", "job_id", "status"),
        Index("ix_recipients_job_id_external_id", "job_id", "external_id"),
        UniqueConstraint("certificate_number", name="uq_recipients_certificate_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )

    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    course_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[RecipientStatus] = mapped_column(
        Enum(
            RecipientStatus,
            name="recipient_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RecipientStatus.PENDING,
    )

    validation_errors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    certificate_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    certificate_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    certificate_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job = relationship("Job", back_populates="recipients")
