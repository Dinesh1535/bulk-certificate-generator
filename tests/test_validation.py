import pytest
from fastapi.testclient import TestClient


def test_validation_empty_recipient_list(client: TestClient):
    """Test creating a job with an empty recipient list fails with 422."""
    payload = {
        "event_name": "AI Workshop",
        "issuer_name": "Test Academy",
        "recipients": []
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_missing_required_fields(client: TestClient):
    """Test creating a job without required event_name and issuer_name fails."""
    payload = {
        "recipients": [
            {"recipient_name": "John Doe", "recipient_email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_invalid_recipient_email(client: TestClient):
    """Test recipient with an invalid email address format fails."""
    payload = {
        "event_name": "Web Dev Summit",
        "issuer_name": "Code Camp",
        "recipients": [
            {"recipient_name": "John Doe", "recipient_email": "invalid-email-format"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


def test_validation_blank_recipient_name(client: TestClient):
    """Test recipient with whitespace-only or empty name fails."""
    payload = {
        "event_name": "Web Dev Summit",
        "issuer_name": "Code Camp",
        "recipients": [
            {"recipient_name": "   ", "recipient_email": "john@example.com"}
        ]
    }
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
