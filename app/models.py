import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    func
)
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"
    FAILED = "FAILED"


class RecipientStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


def generate_uuid() -> str:
    return str(uuid.uuid4())


class CertificateJob(Base):
    """Represents a bulk certificate generation batch job."""
    __tablename__ = "certificate_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    event_name = Column(String(255), nullable=False)
    issuer_name = Column(String(255), nullable=False)
    issue_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(String(32), default=JobStatus.PENDING.value, nullable=False, index=True)
    total_count = Column(Integer, default=0, nullable=False)
    processed_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)

    zip_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    recipients = relationship(
        "RecipientCertificate",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="RecipientCertificate.created_at"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "event_name": self.event_name,
            "issuer_name": self.issuer_name,
            "issue_date": str(self.issue_date),
            "description": self.description,
            "status": self.status,
            "total_count": self.total_count,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "zip_available": bool(self.zip_path),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class RecipientCertificate(Base):
    """Represents an individual recipient certificate within a job."""
    __tablename__ = "recipient_certificates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("certificate_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    certificate_code = Column(String(64), unique=True, index=True, nullable=False)

    custom_attributes = Column(JSON, nullable=True, default=dict)

    status = Column(String(32), default=RecipientStatus.PENDING.value, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    generated_at = Column(DateTime, nullable=True)

    job = relationship("CertificateJob", back_populates="recipients")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "recipient_name": self.recipient_name,
            "recipient_email": self.recipient_email,
            "certificate_code": self.certificate_code,
            "custom_attributes": self.custom_attributes or {},
            "status": self.status,
            "error_message": self.error_message,
            "has_pdf": bool(self.pdf_path),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
