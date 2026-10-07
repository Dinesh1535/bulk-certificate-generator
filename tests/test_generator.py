import os
from pathlib import Path
from datetime import date
import pytest
from app.services.certificate_service import certificate_generator


def test_pdf_generation_success(tmp_path: Path):
    """Test generating a valid PDF file."""
    output_pdf = tmp_path / "test_certificate.pdf"
    result_path = certificate_generator.generate_pdf(
        output_path=output_pdf,
        recipient_name="Marie Curie",
        event_name="Quantum Computing Masterclass",
        issuer_name="European Science Institute",
        certificate_code="CERT-2026-MC001",
        issue_date=date(2026, 5, 20),
        title="Certificate of Excellence",
        description="Awarded for breakthrough contributions to quantum algorithms.",
        custom_attributes={"Grade": "Distinction", "Honors": "Top 1%"}
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000  # Non-trivial PDF size

    # Verify PDF magic bytes (%PDF)
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header.startswith(b"%PDF")


def test_pdf_generation_simulated_failure(tmp_path: Path):
    """Test that the failure simulation hook properly raises an exception."""
    output_pdf = tmp_path / "fail_certificate.pdf"
    with pytest.raises(RuntimeError, match="Simulated generation failure"):
        certificate_generator.generate_pdf(
            output_path=output_pdf,
            recipient_name="Faulty Recipient __FAIL_SIMULATION__",
            event_name="Robotics Expo",
            issuer_name="RoboTech",
            certificate_code="CERT-FAIL-01",
            issue_date=date.today()
        )
