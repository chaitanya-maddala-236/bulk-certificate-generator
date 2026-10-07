from app.utils.validation import validate_recipient_payload


def test_valid_recipient_is_normalized() -> None:
    result = validate_recipient_payload(
        {
            "full_name": "  Alice Johnson ",
            "email": "ALICE@example.com ",
            "course_name": " Generative AI ",
            "external_id": " STU-001 ",
        }
    )

    assert result.is_valid
    assert result.full_name == "Alice Johnson"
    assert result.email == "ALICE@example.com"
    assert result.course_name == "Generative AI"
    assert result.external_id == "STU-001"


def test_invalid_recipient_collects_errors() -> None:
    result = validate_recipient_payload(
        {
            "full_name": " ",
            "email": "not-an-email",
            "course_name": "",
        }
    )

    assert not result.is_valid
    assert "full_name is required" in result.errors
    assert "email must be a valid email address" in result.errors
    assert "course_name is required" in result.errors
