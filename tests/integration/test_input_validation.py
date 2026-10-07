from conftest import sample_payload

from app.core.enums import RecipientStatus


def test_invalid_recipients_are_isolated(client) -> None:
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(
            [
                {
                    "full_name": "Alice Johnson",
                    "email": "alice@example.com",
                    "course_name": "Generative AI",
                },
                {"full_name": "", "email": "bad-email", "course_name": ""},
            ]
        ),
    )

    assert response.status_code == 202
    body = response.json()
    assert body["total_recipients"] == 2
    assert body["valid_recipients"] == 1
    assert body["invalid_recipients"] == 1

    recipients = client.get(f"/api/v1/jobs/{body['job_id']}/recipients").json()["items"]
    invalid = [item for item in recipients if item["status"] == RecipientStatus.INVALID]
    assert len(invalid) == 1
    assert "full_name is required" in invalid[0]["validation_errors"]


def test_too_many_recipients_returns_422(client) -> None:
    recipients = [
        {"full_name": f"Person {index}", "email": None, "course_name": "AI"} for index in range(6)
    ]

    response = client.post("/api/v1/jobs", json=sample_payload(recipients))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_LIMIT_EXCEEDED"
