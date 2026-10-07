from typing import Protocol
from uuid import UUID

from app.core.exceptions import QueueError


class TaskQueue(Protocol):
    def enqueue_generation_job(self, job_id: UUID) -> None: ...


class CeleryTaskQueue:
    def enqueue_generation_job(self, job_id: UUID) -> None:
        try:
            from app.workers.tasks import process_generation_job

            process_generation_job.delay(str(job_id))
        except Exception as exc:  # pragma: no cover - exercised through fake queue tests if needed
            raise QueueError(f"Failed to enqueue generation job: {exc}") from exc
