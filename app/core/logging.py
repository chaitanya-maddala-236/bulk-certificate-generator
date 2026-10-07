import logging
from contextvars import ContextVar

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def configure_logging(level: str = "INFO") -> None:
    original_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = original_factory(*args, **kwargs)
        record.request_id = request_id_ctx.get() or "-"
        return record

    logging.setLogRecordFactory(record_factory)
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
    )
