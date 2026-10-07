from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def engine_options(database_url: str, *, connect_timeout: int = 5) -> dict:
    if database_url.startswith("postgresql"):
        return {"connect_args": {"connect_timeout": connect_timeout}}
    return {}


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    **engine_options(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
