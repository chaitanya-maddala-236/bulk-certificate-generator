# Database Design

## ER Diagram

```mermaid
erDiagram
    JOBS ||--o{ RECIPIENTS : contains

    JOBS {
        uuid id PK
        string organization_name
        string certificate_title
        string event_name
        date issue_date
        string status
        int total_recipients
        int valid_recipients
        int invalid_recipients
        int success_count
        int failure_count
        timestamp created_at
        timestamp started_at
        timestamp completed_at
    }

    RECIPIENTS {
        uuid id PK
        uuid job_id FK
        string full_name
        string email
        string course_name
        string external_id
        string status
        json validation_errors
        string error_message
        string certificate_number
        string certificate_path
        string certificate_filename
        int certificate_size_bytes
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
    }
```

## Tables

### jobs

Stores one submitted bulk request and aggregate counters.

Important fields:

- `id`: UUID primary key and public job identifier.
- `status`: `QUEUED`, `RUNNING`, `COMPLETED`, `COMPLETED_WITH_ERRORS`, or `FAILED`.
- `total_recipients`, `valid_recipients`, `invalid_recipients`: submission counts.
- `success_count`, `failure_count`: generation counts.
- `started_at`, `completed_at`: worker lifecycle timestamps.

### recipients

Stores one recipient row in a job.

Important fields:

- `id`: UUID primary key and public recipient identifier.
- `job_id`: foreign key to `jobs`.
- `status`: `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`, or `INVALID`.
- `validation_errors`: recipient-level validation errors for invalid rows.
- `certificate_path`: relative storage path, never user-provided.
- `certificate_number`: human-readable certificate ID.

## Indexes

- `jobs(status)`
- `jobs(created_at)`
- `recipients(job_id)`
- `recipients(job_id, status)`
- `recipients(job_id, external_id)`
- unique `recipients(certificate_number)`

## Transaction Boundaries

Job creation inserts the job and all recipient rows in one transaction. If insertion fails, no partial job is committed.

Worker processing commits state progressively per recipient. It does not keep one large transaction open while generating many PDFs.

## Why PDFs Are Not Stored in PostgreSQL

PDFs are binary blobs and can grow quickly. Keeping them outside the database makes backups, query performance, and storage scaling simpler. PostgreSQL stores metadata and status; local or object storage stores the file bytes.

## Time Handling

`issue_date` is stored as a date because it is business data printed on certificates. Operational timestamps are timezone-aware and treated as UTC.
