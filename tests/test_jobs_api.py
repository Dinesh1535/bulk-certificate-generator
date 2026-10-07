import io
import time
import zipfile
from fastapi.testclient import TestClient


def test_create_and_process_job_success(client: TestClient):
    """Test full flow: create job, process certificates, check completed status."""
    payload = {
        "title": "Certificate of Achievement",
        "event_name": "Full Stack Cloud Workshop",
        "issuer_name": "Cloud Academy",
        "description": "Excellence in distributed cloud architecture",
        "recipients": [
            {"recipient_name": "Alice Smith", "recipient_email": "alice@example.com", "custom_attributes": {"grade": "A"}},
            {"recipient_name": "Bob Jones", "recipient_email": "bob@example.com", "custom_attributes": {"grade": "B+"}}
        ]
    }

    # 1. Submit Job
    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["total_recipients"] == 2
    job_id = data["job_id"]

    # 2. Check Job Status (FastAPI TestClient executes BackgroundTasks synchronously on exit)
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    assert job_data["status"] == "COMPLETED"
    assert job_data["total_count"] == 2
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 0
    assert job_data["progress_percentage"] == 100.0
    assert len(job_data["recipients"]) == 2

    # Verify recipients have certificate codes and success status
    for r in job_data["recipients"]:
        assert r["status"] == "SUCCESS"
        assert r["has_pdf"] is True
        assert r["certificate_code"].startswith("CERT-")


def test_handle_individual_certificate_failure(client: TestClient):
    """
    Test critical requirement: A failure while generating one certificate should
    NOT prevent other valid certificates in the same job from being generated.
    """
    payload = {
        "title": "Certificate of Completion",
        "event_name": "Resilience & Fault Tolerance Seminar",
        "issuer_name": "Engineering Council",
        "recipients": [
            {"recipient_name": "Valid Recipient One", "recipient_email": "one@example.com"},
            {"recipient_name": "Corrupt Entry __FAIL_SIMULATION__", "recipient_email": "fail@example.com"},
            {"recipient_name": "Valid Recipient Two", "recipient_email": "two@example.com"}
        ]
    }

    response = client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Fetch status
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    # Overall job status should reflect partial success
    assert job_data["status"] == "COMPLETED_WITH_ERRORS"
    assert job_data["total_count"] == 3
    assert job_data["success_count"] == 2
    assert job_data["failed_count"] == 1

    # Verify per-recipient isolation
    recipients = job_data["recipients"]
    successes = [r for r in recipients if r["status"] == "SUCCESS"]
    failures = [r for r in recipients if r["status"] == "FAILED"]

    assert len(successes) == 2
    assert len(failures) == 1
    assert "Simulated generation failure" in failures[0]["error_message"]
    assert failures[0]["has_pdf"] is False


def test_download_individual_certificate(client: TestClient):
    """Test downloading an individual generated certificate PDF."""
    payload = {
        "event_name": "Security Summit",
        "issuer_name": "CyberSec Org",
        "recipients": [
            {"recipient_name": "Diana Prince", "recipient_email": "diana@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Get recipient ID
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    recipient_id = job_res.json()["recipients"][0]["id"]

    # Download PDF
    download_res = client.get(f"/api/v1/jobs/{job_id}/certificates/{recipient_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert len(download_res.content) > 1000
    assert download_res.content.startswith(b"%PDF")


def test_download_all_certificates_zip(client: TestClient):
    """Test downloading all valid certificates for a job as a ZIP archive."""
    payload = {
        "title": "Diplomacy Bootcamp",
        "event_name": "Global Summit",
        "issuer_name": "Diplomatic Academy",
        "recipients": [
            {"recipient_name": "Person A", "recipient_email": "a@example.com"},
            {"recipient_name": "Person B", "recipient_email": "b@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    # Download ZIP
    zip_res = client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_res.status_code == 200
    assert "zip" in zip_res.headers["content-type"]

    # Inspect ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        for filename in namelist:
            assert filename.endswith(".pdf")


def test_certificate_verification_endpoint(client: TestClient):
    """Test public credential verification endpoint."""
    payload = {
        "event_name": "Blockchain & Cryptography",
        "issuer_name": "Crypto Institute",
        "recipients": [
            {"recipient_name": "Satoshi Nakamoto", "recipient_email": "sat@example.com"}
        ]
    }
    create_res = client.post("/api/v1/jobs", json=payload)
    job_id = create_res.json()["job_id"]

    job_data = client.get(f"/api/v1/jobs/{job_id}").json()
    code = job_data["recipients"][0]["certificate_code"]

    # 1. Verify valid code
    verify_res = client.get(f"/api/v1/certificates/verify/{code}")
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["is_valid"] is True
    assert v_data["recipient_name"] == "Satoshi Nakamoto"
    assert v_data["issuer_name"] == "Crypto Institute"

    # 2. Verify invalid code
    invalid_res = client.get("/api/v1/certificates/verify/CERT-INVALID-999")
    assert invalid_res.status_code == 200
    inv_data = invalid_res.json()
    assert inv_data["is_valid"] is False


def test_create_job_via_csv(client: TestClient):
    """Test creating a bulk job by uploading a CSV file."""
    csv_data = (
        "recipient_name,recipient_email,grade\n"
        "Ada Lovelace,ada@computing.org,A+\n"
        "Grace Hopper,grace@navy.mil,A\n"
    )

    files = {
        "file": ("recipients.csv", csv_data.encode("utf-8"), "text/csv")
    }
    data = {
        "title": "Pioneers in Computing",
        "event_name": "Women in Tech",
        "issuer_name": "Tech Foundation"
    }

    response = client.post("/api/v1/jobs/csv", data=data, files=files)
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    # Check job execution
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.status_code == 200
    assert job_res.json()["total_count"] == 2
    assert job_res.json()["status"] == "COMPLETED"
