from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import (
    get_database_session,
    get_settings_dependency,
    get_storage_service,
    get_task_queue,
)
from app.config import Settings
from app.db.base import Base
from app.main import app
from app.services.queue_service import TaskQueue
from app.services.storage_service import LocalFileStorage


class FakeQueue(TaskQueue):
    def __init__(self) -> None:
        self.enqueued: list[UUID] = []

    def enqueue_generation_job(self, job_id: UUID) -> None:
        self.enqueued.append(job_id)


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",
        STORAGE_PATH=tmp_path / "certificates",
        MAX_RECIPIENTS=5,
        PROCESS_BATCH_SIZE=2,
        APP_ENV="test",
    )


@pytest.fixture()
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def fake_queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture()
def client(
    session_factory: sessionmaker[Session],
    settings: Settings,
    fake_queue: FakeQueue,
) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_database_session] = override_db
    app.dependency_overrides[get_settings_dependency] = lambda: settings
    app.dependency_overrides[get_task_queue] = lambda: fake_queue
    app.dependency_overrides[get_storage_service] = lambda: LocalFileStorage(settings.storage_path)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def sample_payload(recipients: list[dict] | None = None) -> dict:
    return {
        "organization_name": "ABC Learning",
        "certificate_title": "Certificate of Completion",
        "event_name": "Advanced AI Workshop",
        "issue_date": "2026-10-07",
        "recipients": recipients
        or [
            {
                "full_name": "Alice Johnson",
                "email": "alice@example.com",
                "course_name": "Generative AI",
                "external_id": "STU-001",
            }
        ],
    }
