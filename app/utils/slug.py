import re


def safe_filename_part(value: str, *, fallback: str = "certificate") -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    return value[:80] or fallback
