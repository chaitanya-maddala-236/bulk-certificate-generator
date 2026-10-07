from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)
class ValidatedRecipient:
    full_name: str | None
    email: str | None
    course_name: str | None
    external_id: str | None
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def validate_recipient_payload(payload: object) -> ValidatedRecipient:
    """Validate one recipient without rejecting the surrounding bulk request."""

    raw = payload if isinstance(payload, dict) else {}
    errors: list[str] = []

    full_name = normalize_optional(raw.get("full_name"))
    email = normalize_optional(raw.get("email"))
    course_name = normalize_optional(raw.get("course_name"))
    external_id = normalize_optional(raw.get("external_id"))

    if not full_name:
        errors.append("full_name is required")
    elif len(full_name) < 2:
        errors.append("full_name must be at least 2 characters")
    elif len(full_name) > 200:
        errors.append("full_name must be at most 200 characters")

    if email:
        if len(email) > 320:
            errors.append("email must be at most 320 characters")
        else:
            try:
                email = validate_email(email, check_deliverability=False).normalized
            except EmailNotValidError:
                errors.append("email must be a valid email address")

    if not course_name:
        errors.append("course_name is required")
    elif len(course_name) > 255:
        errors.append("course_name must be at most 255 characters")

    if external_id and len(external_id) > 255:
        errors.append("external_id must be at most 255 characters")

    return ValidatedRecipient(
        full_name=full_name,
        email=email,
        course_name=course_name,
        external_id=external_id,
        errors=errors,
    )
