from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator


class RecipientInput(BaseModel):
    """Schema for individual recipient input."""
    recipient_name: str = Field(..., min_length=1, max_length=255, description="Full name of recipient")
    recipient_email: EmailStr = Field(..., description="Valid email address of recipient")
    custom_attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata like grade, role, hours")

    @field_validator("recipient_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be blank or whitespace only")
        return trimmed


class CreateJobRequest(BaseModel):
    """Schema for creating a bulk certificate generation job."""
    title: str = Field(
        default="Certificate of Completion",
        min_length=2,
        max_length=255,
        description="Certificate title/heading"
    )
    event_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Name of the course, conference, or workshop"
    )
    issuer_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Name of the organization, institute, or authorized issuer"
    )
    issue_date: Optional[date] = Field(
        default_factory=date.today,
        description="Date of certificate issue (YYYY-MM-DD)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description or commendation text"
    )
    recipients: List[RecipientInput] = Field(
        ...,
        min_length=1,
        description="List of recipients to generate certificates for"
    )


class RecipientSummaryResponse(BaseModel):
    """Lightweight recipient summary."""
    id: str
    recipient_name: str
    recipient_email: str
    certificate_code: str
    status: str
    error_message: Optional[str] = None
    has_pdf: bool
    download_url: Optional[str] = None
    generated_at: Optional[datetime] = None


class JobCreatedResponse(BaseModel):
    """Response returned immediately after submitting a generation job."""
    job_id: str
    status: str
    message: str
    total_recipients: int
    tracking_url: str


class JobDetailResponse(BaseModel):
    """Comprehensive job status and progress response."""
    id: str
    title: str
    event_name: str
    issuer_name: str
    issue_date: date
    description: Optional[str] = None
    status: str
    total_count: int
    processed_count: int
    success_count: int
    failed_count: int
    progress_percentage: float
    zip_available: bool
    zip_download_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    recipients: Optional[List[RecipientSummaryResponse]] = None


class JobListItemResponse(BaseModel):
    """Item schema for listing jobs."""
    id: str
    title: str
    event_name: str
    issuer_name: str
    issue_date: date
    status: str
    total_count: int
    success_count: int
    failed_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class CertificateVerificationResponse(BaseModel):
    """Public certificate verification response."""
    is_valid: bool
    certificate_code: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    event_name: Optional[str] = None
    issuer_name: Optional[str] = None
    issue_date: Optional[date] = None
    status: Optional[str] = None
    generated_at: Optional[datetime] = None
    message: str
