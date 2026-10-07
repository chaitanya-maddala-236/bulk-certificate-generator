from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db
from app.services.queue_service import CeleryTaskQueue, TaskQueue
from app.services.storage_service import LocalFileStorage, StorageService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_task_queue() -> TaskQueue:
    return CeleryTaskQueue()


def get_storage_service(settings: Settings = Depends(get_settings_dependency)) -> StorageService:
    return LocalFileStorage(settings.storage_path)


def get_database_session() -> Generator[Session, None, None]:
    yield from get_db()
