# Design Decisions

## Why FastAPI?

FastAPI gives strong request validation, dependency injection, automatic OpenAPI docs, and a small amount of boilerplate. It is a good fit for a take-home backend API because the code remains readable.

## Why PostgreSQL?

The core data is relational: jobs contain recipients, status queries need indexes, and job creation needs transactional guarantees. PostgreSQL is reliable and production-standard.

## Why Celery + Redis?

Celery separates long-running PDF generation from HTTP request handling. Redis is simple to run locally and works well as a Celery broker for this project.

## Why Asynchronous Processing?

Generating many PDFs can take seconds or minutes and involves CPU work plus filesystem I/O. The API should accept the job quickly and let clients poll durable progress.

## Why Local File Storage?

Local storage keeps the take-home runnable without cloud credentials. The storage service is abstracted so S3 or another object store can replace it later.

## Why Not Store PDFs in PostgreSQL?

The database is optimized here for metadata, counters, and queryable state. Storing files separately keeps database rows smaller and makes file delivery easier.

## Why Polling Instead of WebSockets?

Polling is enough for job progress and much easier to operate. WebSockets can be added later if real-time updates become important.

## Why Per-Recipient Error Isolation?

Bulk workflows commonly contain a few bad rows or renderer edge cases. One failure should not waste successful work for hundreds of other recipients.

## Why UUIDs?

UUIDs are safe public identifiers and avoid leaking table sizes or sequential IDs. They also make filesystem paths independent of user input.

## Why Pagination?

A single job can contain thousands of recipients. Pagination keeps responses bounded and predictable.

## Why Database-Driven Job Status?

The database is durable and queryable. Celery result state is worker infrastructure state, not a complete product-facing progress model.
