# 📜 Bulk Certificate Generator

A high-performance backend API and interactive platform for generating, tracking, and retrieving professional certificates in bulk. Designed for organizations, conferences, and educational institutions issuing certificates to hundreds or thousands of participants.

Built with **FastAPI**, **ReportLab**, and **SQLAlchemy** (SQLite / PostgreSQL ready).

---

## 🌟 Key Features

- **🚀 Asynchronous Bulk Processing:**
  Instant HTTP `202 Accepted` response with tracking URL. Non-blocking certificate generation runs smoothly in background tasks without stalling HTTP request-response cycles.
- **🛡️ Resilient Failure Isolation:**
  Corrupt recipient data or rendering failures on an individual entry **never** cancel or block the generation of other valid recipients in the same batch.
- **🎨 High-Fidelity Vector PDF Engine:**
  ReportLab-powered certificate renderer creating crisp, publication-grade vector PDFs with elegant double borders, ornamental corner accents, official gold seal emblems, and dynamic layout scaling.
- **📦 One-Click Bulk ZIP Retrieval:**
  Effortlessly retrieve all valid certificates in a batch as a single structured `.zip` archive.
- **🔍 Public Verification Portal:**
  Instant verification endpoint (`/api/v1/certificates/verify/{certificate_code}`) enabling employers or institutions to verify the validity of any issued credential.
- **📁 CSV & JSON Ingestion:**
  Supports both structured JSON batch requests and direct CSV file uploads.
- **💻 Interactive Web Dashboard & OpenAPI Docs:**
  Modern glassmorphic UI at `/` and interactive Swagger docs at `/docs`.

---

## 🏗️ System Architecture & Design Decisions

### 1. Framework Choice: FastAPI
- **Why not Flask / Django?**
  - **Asynchronous Execution:** FastAPI has first-class `async` support and built-in `BackgroundTasks`, enabling non-blocking background processing without heavy message brokers for moderate scale.
  - **Schema Validation:** Strict compile-time and runtime validation through **Pydantic v2** ensures malformed inputs are caught immediately before database writes.
  - **Auto-Generated Interactive Documentation:** Live OpenAPI/Swagger documentation (`/docs`) and ReDoc (`/redoc`) make testing endpoints trivial.

### 2. Processing Strategy: Synchronous vs. Background Processing
- **Decision:** Asynchronous background processing (`BackgroundTasks` + State Machine).
- **Justification:**
  - Generating 500+ vector PDF certificates involves file I/O and canvas calculations that can take several seconds to minutes. Keeping an HTTP connection open for this duration risks client timeouts, gateway timeouts (504s), and socket pool exhaustion.
  - The API immediately acknowledges requests with `HTTP 202 Accepted`, assigning a unique `job_id`. Clients can poll progress through `GET /api/v1/jobs/{job_id}` or monitor via WebSockets/polling in the frontend UI.
  - *Extensibility for Enterprise Scale:* The architecture isolates the processing logic in `job_processor.py`. For distributed enterprise scale, this can seamlessly transition to Celery / Redis Queue with zero changes to the core generation logic.

### 3. Failure Handling & Isolation
- A batch job consists of an overall `CertificateJob` record and individual `RecipientCertificate` child records.
- Processing iterates through each recipient in a protected `try...except` block:
  - If recipient generation succeeds: status updates to `SUCCESS`, file path is recorded.
  - If recipient generation fails (e.g. invalid name, rendering error): status updates to `FAILED`, the exact exception message is stored in `error_message`, and the processor moves to the next recipient.
- The overall job status transitions dynamically:
  - `COMPLETED`: All recipients succeeded.
  - `COMPLETED_WITH_ERRORS`: Some succeeded, some failed (with detailed failure inspection).
  - `FAILED`: No recipients succeeded.

### 4. Database: SQLAlchemy Relational Schema
- Standard relational model with foreign keys and cascade deletions.
- Zero-config local **SQLite** default for portability and immediate out-of-the-box execution.
- Switching to **PostgreSQL** or **MySQL** only requires changing the `DATABASE_URL` environment variable.

---

## 📂 Project Structure

```text
Bulk Certificate Generator/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Pydantic Settings & storage directory initialization
│   ├── database.py               # SQLAlchemy engine, session maker, get_db dependency
│   ├── models.py                 # CertificateJob & RecipientCertificate ORM models
│   ├── schemas.py                # Pydantic request/response validation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── certificate_service.py # ReportLab vector PDF rendering engine
│   │   └── job_processor.py      # Background worker with failure isolation & ZIP bundling
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py         # Aggregated v1 API router & /health endpoint
│   │       ├── jobs.py           # Job submission (JSON & CSV), status polling, listing
│   │       └── certificates.py   # PDF download, ZIP download, public verification
│   └── main.py                   # FastAPI app entry point, CORS, static mounts
├── static/                       # Web Dashboard Frontend
│   ├── index.html                # Modern single-page management dashboard
│   ├── css/style.css             # Glassmorphism dark theme styling
│   └── js/app.js                 # Dynamic polling, drag-and-drop CSV, live preview
├── storage/                      # Local filesystem storage (auto-created)
│   ├── certificates/             # Generated PDF files
│   └── zips/                     # Pre-packaged bulk ZIP archives
├── tests/                        # Comprehensive Pytest Suite
│   ├── __init__.py
│   ├── conftest.py               # Test db fixtures & isolated storage setup
│   ├── test_validation.py        # Schema constraint & input validation tests
│   ├── test_generator.py         # ReportLab PDF generation unit tests
│   └── test_jobs_api.py          # End-to-end API tests (create, poll, fail, download, ZIP)
├── sample_recipients.csv         # Sample CSV for quick testing
├── sample_request.json           # Sample JSON payload
├── requirements.txt              # Production and test dependencies
├── pytest.ini                    # Pytest environment configuration
├── .env.example                  # Environment configuration template
└── README.md                     # Comprehensive documentation
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 1. Clone & Navigate to Directory
```bash
cd "Bulk Certificate Generator"
```

### 2. Create Virtual Environment & Activate
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Running the Application

### Start Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive Web Dashboard:** Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.
- **Interactive OpenAPI (Swagger UI):** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
- **Alternative ReDoc UI:** Open [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

---

## 🧪 Running Automated Tests

A comprehensive test suite using `pytest` is included:
```bash
pytest -v
```

### Tests Covered:
1. `test_validation.py`: Empty lists, blank recipient names, invalid email formats, missing required fields.
2. `test_generator.py`: PDF creation, non-empty binary checks, valid PDF header magic bytes, simulated error hook.
3. `test_jobs_api.py`:
   - Creating a bulk generation job (HTTP 202 Accepted).
   - Polling job status through to completion.
   - **Isolated failure handling**: Ensuring failing entries do not stop valid certificates in the same batch.
   - Individual certificate PDF download.
   - Bulk ZIP archive generation & file integrity check.
   - Public credential verification endpoint.
   - CSV upload processing.

---

## 📡 API Reference & Usage Guide

### 1. Submit Generation Job (JSON)

**Endpoint:** `POST /api/v1/jobs`  
**Status:** `202 Accepted`

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Certificate of Excellence",
    "event_name": "Distributed Systems Bootcamp 2026",
    "issuer_name": "Tech Institute",
    "issue_date": "2026-10-07",
    "description": "For demonstrating exceptional mastery of backend engineering.",
    "recipients": [
      {
        "recipient_name": "Grace Hopper",
        "recipient_email": "grace@example.com",
        "custom_attributes": { "grade": "Distinction", "hours": 40 }
      },
      {
        "recipient_name": "Alan Turing",
        "recipient_email": "alan@example.com",
        "custom_attributes": { "grade": "Honors", "hours": 45 }
      }
    ]
  }'
```

**Response:**
```json
{
  "job_id": "936d59ce-0ad6-407a-9a9d-5bc971b86e42",
  "status": "PENDING",
  "message": "Generation job created for 2 recipients. Processing started in background.",
  "total_recipients": 2,
  "tracking_url": "/api/v1/jobs/936d59ce-0ad6-407a-9a9d-5bc971b86e42"
}
```

---

### 2. Submit Generation Job (CSV Upload)

**Endpoint:** `POST /api/v1/jobs/csv`  
**Status:** `202 Accepted`

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/csv" \
  -F "file=@sample_recipients.csv" \
  -F "title=Certificate of Completion" \
  -F "event_name=Cloud Engineering Summit" \
  -F "issuer_name=DevOps Global"
```

---

### 3. Check Job Status & Progress

**Endpoint:** `GET /api/v1/jobs/{job_id}`

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/936d59ce-0ad6-407a-9a9d-5bc971b86e42"
```

**Response:**
```json
{
  "id": "936d59ce-0ad6-407a-9a9d-5bc971b86e42",
  "title": "Certificate of Excellence",
  "event_name": "Distributed Systems Bootcamp 2026",
  "issuer_name": "Tech Institute",
  "issue_date": "2026-10-07",
  "status": "COMPLETED",
  "total_count": 2,
  "processed_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "zip_available": true,
  "zip_download_url": "/api/v1/jobs/936d59ce-0ad6-407a-9a9d-5bc971b86e42/download-all",
  "recipients": [
    {
      "id": "cf603a11-5820-4322-a968-3e4cbff5521b",
      "recipient_name": "Grace Hopper",
      "recipient_email": "grace@example.com",
      "certificate_code": "CERT-2026-A1B2C3D4",
      "status": "SUCCESS",
      "error_message": null,
      "has_pdf": true,
      "download_url": "/api/v1/jobs/936d59ce-0ad6-407a-9a9d-5bc971b86e42/certificates/cf603a11-5820-4322-a968-3e4cbff5521b/download"
    }
  ]
}
```

---

### 4. Retrieve Individual Certificate PDF

**Endpoint:** `GET /api/v1/jobs/{job_id}/certificates/{recipient_id}/download`

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/jobs/{job_id}/certificates/{recipient_id}/download"
```

---

### 5. Retrieve All Certificates as ZIP Archive

**Endpoint:** `GET /api/v1/jobs/{job_id}/download-all`

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/jobs/{job_id}/download-all"
```

---

### 6. Public Certificate Verification

**Endpoint:** `GET /api/v1/certificates/verify/{certificate_code}`

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificates/verify/CERT-2026-A1B2C3D4"
```

**Response:**
```json
{
  "is_valid": true,
  "certificate_code": "CERT-2026-A1B2C3D4",
  "recipient_name": "Grace Hopper",
  "recipient_email": "grace@example.com",
  "event_name": "Distributed Systems Bootcamp 2026",
  "issuer_name": "Tech Institute",
  "issue_date": "2026-10-07",
  "status": "SUCCESS",
  "message": "Official certificate successfully verified."
}
```

---

## 💡 Interview Discussion & Talking Points

During an interview, be prepared to explain:

1. **Why Asynchronous over Synchronous?**
   - Synchronous generation would tie up server worker threads with CPU/disk I/O, quickly exhausting available connections. By using non-blocking background workers and returning `202 Accepted`, response times are instantaneous (`< 20ms`), and client applications remain responsive.
2. **How Failure Isolation is Guaranteed:**
   - In `JobProcessor.process_job()`, each recipient is handled in an independent `try...except` scope. State changes are committed per-recipient or in micro-batches, so that a process crash or exception on item $N$ does not roll back item $N-1$ or abort item $N+1$.
3. **Template Vector Rendering:**
   - Instead of raster images or external HTML headless browsers (which incur heavy RAM overhead and require system C-libraries), ReportLab builds lightweight, crisp vector PDFs mathematically drawn with resolution-independent vector shapes, text, and seals.
4. **How to Scale to 100,000+ Certificates:**
   - Replace FastAPI's in-process `BackgroundTasks` with a distributed task queue like **Celery** or **ARQ** backed by **Redis** or **RabbitMQ**.
   - Store generated PDFs on S3 / Google Cloud Storage instead of local filesystem storage, saving presigned URLs to the database.
   - Use multi-worker PDF rendering processes across Kubernetes pods.
