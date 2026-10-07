import logging
import zipfile
import re
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models import CertificateJob, RecipientCertificate, JobStatus, RecipientStatus
from app.services.certificate_service import certificate_generator

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Sanitize a recipient name for safe file naming."""
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return re.sub(r'[-\s]+', '_', clean)


class JobProcessor:
    """Handles asynchronous bulk generation of certificates with failure isolation."""

    @classmethod
    def process_job(cls, job_id: str) -> None:
        """
        Executes generation for all recipients in a job.
        Runs in background worker or FastAPI BackgroundTasks.
        Guarantees isolation: failure on any recipient never stops other recipients.
        """
        db: Session = SessionLocal()
        try:
            job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found for processing.")
                return

            job.status = JobStatus.IN_PROGRESS.value
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

            recipients = (
                db.query(RecipientCertificate)
                .filter(RecipientCertificate.job_id == job_id)
                .all()
            )

            job.total_count = len(recipients)
            job.processed_count = 0
            job.success_count = 0
            job.failed_count = 0
            db.commit()

            for recipient in recipients:
                recipient.status = RecipientStatus.GENERATING.value
                db.commit()

                try:
                    # Validate recipient attributes
                    if not recipient.recipient_name or not recipient.recipient_name.strip():
                        raise ValueError("Recipient name cannot be empty")
                    if not recipient.recipient_email or "@" not in recipient.recipient_email:
                        raise ValueError(f"Invalid email address: '{recipient.recipient_email}'")

                    # Output filename
                    clean_name = sanitize_filename(recipient.recipient_name)
                    pdf_filename = f"{clean_name}_{recipient.certificate_code}.pdf"
                    pdf_path = settings.CERTIFICATES_DIR / f"{job_id}_{recipient.id}_{pdf_filename}"

                    certificate_generator.generate_pdf(
                        output_path=pdf_path,
                        recipient_name=recipient.recipient_name,
                        event_name=job.event_name,
                        issuer_name=job.issuer_name,
                        certificate_code=recipient.certificate_code,
                        issue_date=job.issue_date,
                        title=job.title,
                        description=job.description,
                        custom_attributes=recipient.custom_attributes,
                    )

                    recipient.status = RecipientStatus.SUCCESS.value
                    recipient.pdf_path = str(pdf_path)
                    recipient.error_message = None
                    recipient.generated_at = datetime.now(timezone.utc)
                    job.success_count += 1

                except Exception as exc:
                    logger.warning(
                        f"Error generating certificate for recipient {recipient.id} ({recipient.recipient_name}): {exc}"
                    )
                    recipient.status = RecipientStatus.FAILED.value
                    recipient.error_message = str(exc)
                    recipient.pdf_path = None
                    job.failed_count += 1

                finally:
                    job.processed_count += 1
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()

            # Final job status determination
            if job.failed_count == 0 and job.success_count > 0:
                job.status = JobStatus.COMPLETED.value
            elif job.success_count > 0 and job.failed_count > 0:
                job.status = JobStatus.COMPLETED_WITH_ERRORS.value
            else:
                job.status = JobStatus.FAILED.value

            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

            # Pre-generate ZIP package if any certificates were successfully generated
            if job.success_count > 0:
                cls.build_zip_archive(job.id, db)

        except Exception as exc:
            logger.exception(f"Unexpected error while processing job {job_id}: {exc}")
            if job:
                job.status = JobStatus.FAILED.value
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    @classmethod
    def build_zip_archive(cls, job_id: str, db: Session) -> Path:
        """Packages all successful certificate PDFs for a job into a ZIP archive."""
        job = db.query(CertificateJob).filter(CertificateJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")

        zip_filename = f"certificates_{sanitize_filename(job.title)}_{job.id[:8]}.zip"
        zip_path = settings.ZIPS_DIR / zip_filename

        successful_recipients = (
            db.query(RecipientCertificate)
            .filter(
                RecipientCertificate.job_id == job_id,
                RecipientCertificate.status == RecipientStatus.SUCCESS.value,
                RecipientCertificate.pdf_path.isnot(None),
            )
            .all()
        )

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in successful_recipients:
                if r.pdf_path and Path(r.pdf_path).exists():
                    archive_name = Path(r.pdf_path).name
                    # Strip leading job_id prefix for clean naming inside ZIP
                    parts = archive_name.split("_", 2)
                    clean_archive_name = parts[-1] if len(parts) >= 3 else archive_name
                    zf.write(r.pdf_path, arcname=clean_archive_name)

        job.zip_path = str(zip_path)
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        return zip_path


job_processor = JobProcessor()
