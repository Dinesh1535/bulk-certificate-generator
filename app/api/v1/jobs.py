import io
import csv
import uuid
import secrets
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CertificateJob, RecipientCertificate, JobStatus, RecipientStatus
from app.schemas import (
    CreateJobRequest,
    JobCreatedResponse,
    JobDetailResponse,
    JobListItemResponse,
    RecipientSummaryResponse,
    RecipientInput,
)
from app.services.job_processor import job_processor

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def generate_certificate_code() -> str:
    """Generate an official unique credential verification code."""
    year = date.today().year
    token = secrets.token_hex(4).upper()
    return f"CERT-{year}-{token}"


@router.post(
    "",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Bulk Certificate Generation Job (JSON)",
    description="Submit a list of recipients along with event details to start generating certificates asynchronously."
)
def create_bulk_certificate_job(
    payload: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if not payload.recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recipient list cannot be empty."
        )

    # 1. Create Job record
    job_id = str(uuid.uuid4())
    job = CertificateJob(
        id=job_id,
        title=payload.title,
        event_name=payload.event_name,
        issuer_name=payload.issuer_name,
        issue_date=payload.issue_date or date.today(),
        description=payload.description,
        status=JobStatus.PENDING.value,
        total_count=len(payload.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0,
    )
    db.add(job)

    # 2. Create Recipient records
    for item in payload.recipients:
        recipient = RecipientCertificate(
            id=str(uuid.uuid4()),
            job_id=job_id,
            recipient_name=item.recipient_name,
            recipient_email=str(item.recipient_email),
            certificate_code=generate_certificate_code(),
            custom_attributes=item.custom_attributes or {},
            status=RecipientStatus.PENDING.value,
        )
        db.add(recipient)

    db.commit()
    db.refresh(job)

    # 3. Schedule generation in background
    background_tasks.add_task(job_processor.process_job, job_id)

    return JobCreatedResponse(
        job_id=job.id,
        status=job.status,
        message=f"Generation job created for {len(payload.recipients)} recipients. Processing started in background.",
        total_recipients=job.total_count,
        tracking_url=f"/api/v1/jobs/{job.id}"
    )


@router.post(
    "/csv",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create Bulk Certificate Job via CSV Upload",
    description="Upload a CSV file containing recipient names and emails to trigger bulk generation."
)
async def create_job_from_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="CSV file with columns: recipient_name, recipient_email"),
    event_name: str = Form(..., description="Course or Event Name"),
    issuer_name: str = Form(..., description="Organization or Issuer Name"),
    title: str = Form("Certificate of Completion", description="Certificate Title"),
    issue_date_val: Optional[str] = Form(None, description="Issue date in YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid .csv file"
        )

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file appears to be empty or unreadable")

    # Normalize column names
    field_map = {col.strip().lower(): col for col in reader.fieldnames}
    name_col = next((field_map[k] for k in ["recipient_name", "name", "full_name"] if k in field_map), None)
    email_col = next((field_map[k] for k in ["recipient_email", "email", "email_address"] if k in field_map), None)

    if not name_col or not email_col:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain headers for recipient name and email (e.g. 'recipient_name,recipient_email' or 'name,email')"
        )

    parsed_recipients: List[RecipientInput] = []
    for idx, row in enumerate(reader, start=1):
        r_name = (row.get(name_col) or "").strip()
        r_email = (row.get(email_col) or "").strip()
        if not r_name and not r_email:
            continue  # skip blank lines

        # Extract extra metadata columns if any
        extra = {k: v for k, v in row.items() if k not in [name_col, email_col] and v}

        try:
            parsed_recipients.append(
                RecipientInput(
                    recipient_name=r_name,
                    recipient_email=r_email,
                    custom_attributes=extra
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Validation failed on CSV row {idx} ({r_name}, {r_email}): {e}"
            )

    if not parsed_recipients:
        raise HTTPException(status_code=422, detail="No valid recipients found in CSV.")

    parsed_date = date.today()
    if issue_date_val:
        try:
            parsed_date = date.fromisoformat(issue_date_val)
        except ValueError:
            pass

    req = CreateJobRequest(
        title=title,
        event_name=event_name,
        issuer_name=issuer_name,
        issue_date=parsed_date,
        recipients=parsed_recipients
    )

    return create_bulk_certificate_job(req, background_tasks, db)


@router.get(
    "",
    response_model=List[JobListItemResponse],
    summary="List Certificate Generation Jobs",
    description="Retrieve a paginated list of previous certificate generation jobs."
)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(CertificateJob)
    if status_filter:
        query = query.filter(CertificateJob.status == status_filter.upper())

    jobs = query.order_by(CertificateJob.created_at.desc()).offset(skip).limit(limit).all()
    return [
        JobListItemResponse(
            id=j.id,
            title=j.title,
            event_name=j.event_name,
            issuer_name=j.issuer_name,
            issue_date=j.issue_date,
            status=j.status,
            total_count=j.total_count,
            success_count=j.success_count,
            failed_count=j.failed_count,
            created_at=j.created_at,
            completed_at=j.completed_at
        )
        for j in jobs
    ]


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get Job Status and Progress",
    description="Poll current progress, overall status, counts, and recipient details for a specific job."
)
def get_job_status(
    job_id: str,
    include_recipients: bool = Query(True, description="Whether to include the full recipient list"),
    db: Session = Depends(get_db)
):
    job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")

    progress_pct = (
        round((job.processed_count / job.total_count) * 100, 1)
        if job.total_count > 0
        else 0.0
    )

    recipient_summaries = None
    if include_recipients:
        recipients = (
            db.query(RecipientCertificate)
            .filter(RecipientCertificate.job_id == job_id)
            .order_by(RecipientCertificate.created_at.asc())
            .all()
        )
        recipient_summaries = [
            RecipientSummaryResponse(
                id=r.id,
                recipient_name=r.recipient_name,
                recipient_email=r.recipient_email,
                certificate_code=r.certificate_code,
                status=r.status,
                error_message=r.error_message,
                has_pdf=bool(r.pdf_path),
                download_url=f"/api/v1/jobs/{job.id}/certificates/{r.id}/download" if r.pdf_path else None,
                generated_at=r.generated_at
            )
            for r in recipients
        ]

    zip_url = f"/api/v1/jobs/{job.id}/download-all" if job.success_count > 0 else None

    return JobDetailResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        issue_date=job.issue_date,
        description=job.description,
        status=job.status,
        total_count=job.total_count,
        processed_count=job.processed_count,
        success_count=job.success_count,
        failed_count=job.failed_count,
        progress_percentage=progress_pct,
        zip_available=bool(job.zip_path) or (job.success_count > 0),
        zip_download_url=zip_url,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        recipients=recipient_summaries
    )
