# Demo Screens

The demo dashboard is intentionally thin. It exists to demonstrate backend behavior, not to duplicate backend business logic.

## 1. Jobs Dashboard

Purpose: show all generation jobs and their progress.

```text
+--------------------------------------------------------------+
| Bulk Certificate Generator                   + Create Job    |
+--------------------------------------------------------------+
| Search jobs...                      Status: [All v]          |
|                                                              |
| ------------------------------------------------------------ |
| Job ID     Event              Status       Progress  Created |
| ------------------------------------------------------------ |
| #8f21      AI Workshop        COMPLETED    100%      Oct 07 |
| #0ab4      Python Course      RUNNING       64%      Oct 07 |
| #9912      ML Bootcamp        WITH ERRORS  100%      Oct 06 |
| ------------------------------------------------------------ |
+--------------------------------------------------------------+
```

Backend APIs:

- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`

## 2. Create Job

Purpose: submit a bulk generation request.

```text
+--------------------------------------------------------------+
| Create Certificate Generation Job                            |
+--------------------------------------------------------------+
| Organization                                                 |
| [ ABC Learning                                      ]         |
| Certificate Title                                            |
| [ Certificate of Completion                         ]         |
| Event Name                                                   |
| [ Advanced AI Workshop                              ]         |
| Issue Date                                                   |
| [ 2026-10-07                                        ]         |
| Recipients JSON                                              |
| [ { ... }                                           ]         |
| [ Submit Generation Job ]                                    |
+--------------------------------------------------------------+
```

Backend API:

- `POST /api/v1/jobs`

## 3. Job Detail

Purpose: monitor processing and see recipient statuses.

```text
+--------------------------------------------------------------+
| <- Jobs     Generation Job #8f21                             |
+--------------------------------------------------------------+
| Advanced AI Workshop                                         |
| ABC Learning                                                 |
| Status: RUNNING                                              |
|                                                              |
| [###############.......] 64%                                 |
|                                                              |
| Total       Valid       Success      Failed      Invalid     |
| 100         95          61           3           5           |
|                                                              |
| ------------------------------------------------------------ |
| Recipient             Status           Certificate           |
| ------------------------------------------------------------ |
| Alice Johnson         SUCCESS          Download              |
| Bob Smith             SUCCESS          Download              |
| Charlie Brown         FAILED           Error                 |
| David Lee             INVALID          Validation Error      |
+--------------------------------------------------------------+
```

Backend APIs:

- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/recipients`

## 4. Recipient Detail

Purpose: inspect one recipient and its failure or certificate metadata.

```text
+--------------------------------------------------------------+
| Recipient                                                    |
| Alice Johnson                                                |
| Email                 alice@example.com                      |
| Course                Generative AI                          |
| Status                SUCCESS                                |
| Certificate ID        CERT-2026-A83F72C1                     |
| Generated At          2026-10-07 15:23:11                    |
| [ Download Certificate ]                                     |
+--------------------------------------------------------------+
```

Backend APIs:

- `GET /api/v1/jobs/{job_id}/recipients/{recipient_id}`
- `GET /api/v1/jobs/{job_id}/recipients/{recipient_id}/certificate`

## 5. Certificate Viewer

Purpose: show a generated PDF in the browser and allow download.

```text
+--------------------------------------------------------------+
| Certificate                                                  |
+--------------------------------------------------------------+
|                                                              |
|                    [ PDF PREVIEW ]                           |
|                                                              |
|                      [Download]                              |
+--------------------------------------------------------------+
```

Backend API:

- `GET /api/v1/jobs/{job_id}/recipients/{recipient_id}/certificate`
