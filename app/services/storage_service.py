import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.core.exceptions import StorageError


@dataclass(frozen=True)
class StoredFile:
    relative_path: str
    filename: str
    size_bytes: int
    absolute_path: Path


class StorageService(Protocol):
    def save(self, job_id: UUID, recipient_id: UUID, content: bytes) -> StoredFile: ...

    def exists(self, relative_path: str) -> bool: ...

    def resolve(self, relative_path: str) -> Path: ...


class LocalFileStorage:
    """Local filesystem storage using UUID paths and atomic replacement."""

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path.resolve()
        self.root_path.mkdir(parents=True, exist_ok=True)

    def save(self, job_id: UUID, recipient_id: UUID, content: bytes) -> StoredFile:
        filename = f"{recipient_id}.pdf"
        job_dir = self.root_path / str(job_id)
        target_path = (job_dir / filename).resolve()

        self._ensure_within_root(target_path)
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            fd, temp_name = tempfile.mkstemp(prefix=f".{recipient_id}.", suffix=".tmp", dir=job_dir)
            with os.fdopen(fd, "wb") as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_name, target_path)
            size = target_path.stat().st_size
        except Exception as exc:
            raise StorageError(f"Failed to save certificate: {exc}") from exc

        relative = target_path.relative_to(self.root_path).as_posix()
        return StoredFile(
            relative_path=relative,
            filename=filename,
            size_bytes=size,
            absolute_path=target_path,
        )

    def exists(self, relative_path: str) -> bool:
        try:
            return self.resolve(relative_path).is_file()
        except StorageError:
            return False

    def resolve(self, relative_path: str) -> Path:
        target = (self.root_path / relative_path).resolve()
        self._ensure_within_root(target)
        return target

    def _ensure_within_root(self, path: Path) -> None:
        try:
            path.relative_to(self.root_path)
        except ValueError as exc:
            raise StorageError("Unsafe certificate path was rejected") from exc
