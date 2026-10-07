"""Initial schema for bulk certificate generation.

Revision ID: 20261007_0001
Revises:
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261007_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

job_status = postgresql.ENUM(
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "COMPLETED_WITH_ERRORS",
    "FAILED",
    name="job_status",
    create_type=False,
)

recipient_status = postgresql.ENUM(
    "PENDING",
    "PROCESSING",
    "SUCCESS",
    "FAILED",
    "INVALID",
    name="recipient_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    job_status.create(bind, checkfirst=True)
    recipient_status.create(bind, checkfirst=True)

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("certificate_title", sa.String(length=255), nullable=False),
        sa.Column("event_name", sa.String(length=255), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("total_recipients", sa.Integer(), nullable=False),
        sa.Column("valid_recipients", sa.Integer(), nullable=False),
        sa.Column("invalid_recipients", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"], unique=False)
    op.create_index("ix_jobs_status", "jobs", ["status"], unique=False)

    op.create_table(
        "recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("course_name", sa.String(length=255), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("status", recipient_status, nullable=False),
        sa.Column("validation_errors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("certificate_number", sa.String(length=64), nullable=True),
        sa.Column("certificate_path", sa.String(length=500), nullable=True),
        sa.Column("certificate_filename", sa.String(length=255), nullable=True),
        sa.Column("certificate_size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_number", name="uq_recipients_certificate_number"),
    )
    op.create_index("ix_recipients_job_id", "recipients", ["job_id"], unique=False)
    op.create_index(
        "ix_recipients_job_id_external_id",
        "recipients",
        ["job_id", "external_id"],
        unique=False,
    )
    op.create_index(
        "ix_recipients_job_id_status",
        "recipients",
        ["job_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_recipients_job_id_status", table_name="recipients")
    op.drop_index("ix_recipients_job_id_external_id", table_name="recipients")
    op.drop_index("ix_recipients_job_id", table_name="recipients")
    op.drop_table("recipients")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_table("jobs")

    recipient_status.drop(op.get_bind(), checkfirst=True)
    job_status.drop(op.get_bind(), checkfirst=True)
