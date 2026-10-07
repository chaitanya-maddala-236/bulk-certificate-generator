from fastapi import APIRouter, Depends, Response, status
from redis import Redis
from sqlalchemy import create_engine, text

from app.api.dependencies import get_settings_dependency
from app.config import Settings
from app.db.session import engine_options

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(
    response: Response,
    settings: Settings = Depends(get_settings_dependency),
) -> dict[str, object]:
    checks: dict[str, str] = {}

    readiness_engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        **engine_options(settings.database_url, connect_timeout=1),
    )
    try:
        with readiness_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    finally:
        readiness_engine.dispose()

    try:
        Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1).ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    if any(value != "ok" for value in checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "checks": checks}

    return {"status": "ok", "checks": checks}
