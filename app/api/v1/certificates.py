from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CertificateJob, RecipientCertificate, RecipientStatus
from app.schemas import CertificateVerificationResponse
from app.services.job_processor import job_processor, sanitize_filename

router = APIRouter(tags=["Certificates & Downloads"])


@router.get(
    "/jobs/{job_id}/certificates/{recipient_id}/download",
    summary="Download Individual Certificate PDF",
    description="Stream or download a specific generated certificate PDF file."
)
def download_single_certificate(
    job_id: str,
    recipient_id: str,
    db: Session = Depends(get_db)
):
    recipient = (
        db.query(RecipientCertificate)
        .filter(
            RecipientCertificate.job_id == job_id,
            RecipientCertificate.id == recipient_id
        )
        .first()
    )

    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient record '{recipient_id}' not found in job '{job_id}'."
        )

    if recipient.status != RecipientStatus.SUCCESS.value or not recipient.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate for recipient has not been successfully generated. Current status: {recipient.status}"
        )

    pdf_file = Path(recipient.pdf_path)
    if not pdf_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated certificate file was not found on server storage."
        )

    clean_name = sanitize_filename(recipient.recipient_name)
    download_filename = f"{clean_name}_{recipient.certificate_code}.pdf"

    return FileResponse(
        path=str(pdf_file),
        media_type="application/pdf",
        filename=download_filename
    )


@router.get(
    "/jobs/{job_id}/download-all",
    summary="Download All Certificates (ZIP Archive)",
    description="Download a zip archive containing all successfully generated certificates for a job."
)
def download_all_certificates(
    job_id: str,
    db: Session = Depends(get_db)
):
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    if job.success_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No certificates have been successfully generated for this job yet. Status: {job.status}"
        )

    # Check if zip exists or generate/regenerate it
    zip_path = Path(job.zip_path) if job.zip_path else None
    if not zip_path or not zip_path.exists():
        zip_path = job_processor.build_zip_archive(job.id, db)

    download_name = f"Certificates_{sanitize_filename(job.title)}_{job.id[:8]}.zip"
    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=download_name
    )


@router.get(
    "/certificates/verify/{certificate_code}",
    response_model=CertificateVerificationResponse,
    summary="Verify Certificate Authenticity",
    description="Public endpoint to verify whether a credential code is authentic and belongs to a genuine recipient."
)
def verify_certificate(
    certificate_code: str,
    db: Session = Depends(get_db)
):
    code_normalized = certificate_code.strip().upper()
    recipient = (
        db.query(RecipientCertificate)
        .filter(RecipientCertificate.certificate_code == code_normalized)
        .first()
    )

    if not recipient:
        return CertificateVerificationResponse(
            is_valid=False,
            certificate_code=code_normalized,
            message="Certificate ID not found. This credential may be invalid or forged."
        )

    job = recipient.job

    return CertificateVerificationResponse(
        is_valid=(recipient.status == RecipientStatus.SUCCESS.value),
        certificate_code=recipient.certificate_code,
        recipient_name=recipient.recipient_name,
        recipient_email=recipient.recipient_email,
        event_name=job.event_name if job else None,
        issuer_name=job.issuer_name if job else None,
        issue_date=job.issue_date if job else None,
        status=recipient.status,
        generated_at=recipient.generated_at,
        message="Official certificate successfully verified." if recipient.status == RecipientStatus.SUCCESS.value else f"Certificate status is {recipient.status}"
    )
