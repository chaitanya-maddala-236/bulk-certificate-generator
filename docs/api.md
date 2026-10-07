# API Documentation

All application endpoints are prefixed with `/api/v1` except health checks.

Error responses use this shape:

```json
{
  "error": {
    "code": "CERTIFICATE_NOT_READY",
    "message": "Certificate has not been successfully generated yet.",
    "request_id": "8e6f..."
  }
}
```

## POST /api/v1/jobs

Creates a bulk certificate generation job.

Returns `202 Accepted`.

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "ABC Learning",
    "certificate_title": "Certificate of Completion",
    "event_name": "Advanced AI Workshop",
    "issue_date": "2026-10-07",
    "recipients": [
      {
        "full_name": "Alice Johnson",
        "email": "alice@example.com",
        "course_name": "Generative AI",
        "external_id": "STU-001"
      }
    ]
  }'
```

Response:

```json
{
  "job_id": "uuid",
  "status": "QUEUED",
  "total_recipients": 1,
  "valid_recipients": 1,
  "invalid_recipients": 0,
  "status_url": "/api/v1/jobs/<job_id>"
}
```

Errors:

- `422 VALIDATION_ERROR` for invalid job-level fields.
- `422 REQUEST_LIMIT_EXCEEDED` when recipient count exceeds `MAX_RECIPIENTS`.

## GET /api/v1/jobs

Lists generation jobs.

Query parameters:

- `page`, default `1`
- `page_size`, default `20`, max `100`
- `status`, optional job status filter

```bash
curl "http://localhost:8000/api/v1/jobs?status=RUNNING&page=1&page_size=20"
```

## GET /api/v1/jobs/{job_id}

Returns job progress and aggregate status.

```bash
curl http://localhost:8000/api/v1/jobs/<JOB_ID>
```

Response fields include:

- `total_recipients`
- `valid_recipients`
- `invalid_recipients`
- `success_count`
- `failure_count`
- `processed_count`
- `progress_percent`
- timestamps

Errors:

- `404 JOB_NOT_FOUND`

## GET /api/v1/jobs/{job_id}/recipients

Lists recipients for one job.

Query parameters:

- `page`, default `1`
- `page_size`, default `50`, max `200`
- `status`, optional recipient status filter

```bash
curl "http://localhost:8000/api/v1/jobs/<JOB_ID>/recipients?status=FAILED&page=1&page_size=50"
```

Response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 50,
  "total": 0
}
```

Errors:

- `404 JOB_NOT_FOUND`

## GET /api/v1/jobs/{job_id}/recipients/{recipient_id}

Returns one recipient detail.

```bash
curl http://localhost:8000/api/v1/jobs/<JOB_ID>/recipients/<RECIPIENT_ID>
```

Errors:

- `404 RECIPIENT_NOT_FOUND`

## GET /api/v1/jobs/{job_id}/recipients/{recipient_id}/certificate

Downloads a generated PDF certificate.

```bash
curl \
  http://localhost:8000/api/v1/jobs/<JOB_ID>/recipients/<RECIPIENT_ID>/certificate \
  --output certificate.pdf
```

Successful response:

- `200 OK`
- `Content-Type: application/pdf`
- `Content-Disposition: attachment`

Errors:

- `404 RECIPIENT_NOT_FOUND`
- `409 CERTIFICATE_NOT_READY` for `PENDING`, `PROCESSING`, `INVALID`, or `FAILED` recipients.
- `500 STORAGE_ERROR` if the database says a certificate exists but the file is missing.

## GET /health/live

Liveness check.

```json
{
  "status": "ok"
}
```

## GET /health/ready

Readiness check for database and Redis.

Returns `503` if a dependency is unavailable.

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```
