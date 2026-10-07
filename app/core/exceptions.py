from http import HTTPStatus


class AppError(Exception):
    """Base application exception rendered as a consistent JSON error response."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: dict | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}


class JobNotFound(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "JOB_NOT_FOUND"
    message = "Generation job was not found."


class RecipientNotFound(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "RECIPIENT_NOT_FOUND"
    message = "Recipient was not found for this job."


class CertificateNotReady(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "CERTIFICATE_NOT_READY"
    message = "Certificate has not been successfully generated yet."


class CertificateGenerationError(AppError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    code = "CERTIFICATE_GENERATION_ERROR"
    message = "Certificate generation failed."


class StorageError(AppError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    code = "STORAGE_ERROR"
    message = "Certificate storage failed."


class QueueError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "QUEUE_ERROR"
    message = "The job could not be enqueued for background processing."


class RequestLimitExceeded(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "REQUEST_LIMIT_EXCEEDED"
    message = "The request exceeds a configured application limit."
