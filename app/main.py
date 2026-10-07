from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize storage directories
    settings.init_storage()
    # Create DB tables
    init_db()
    yield


app = FastAPI(
    title="Bulk Certificate Generator API",
    description="""
## Bulk Certificate Generator

A high-performance backend API and platform that accepts certificate generation requests for large recipient batches, validates recipient data, creates high-resolution vector PDF certificates, provides asynchronous status tracking, and offers individual and bulk ZIP certificate retrieval.

### Key Capabilities:
- 🚀 **Asynchronous Bulk Processing**: Non-blocking generation with instant job acceptance (HTTP 202).
- 🛡️ **Failure Isolation**: An error in an individual recipient never impedes the remainder of the batch.
- 📜 **Professional PDF Engine**: ReportLab vector certificate rendering with custom seals and verifiable credential IDs.
- 📦 **Bulk ZIP Retrieval**: One-click download of all generated certificates in a single archive.
- 🔍 **Public Verification**: Fast public endpoint to verify credential authenticity.
- 💻 **Interactive Dashboard**: Modern web UI for drag-and-drop CSV uploads, live progress tracking, and certificate downloads.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Router
app.include_router(api_router, prefix="/api")

# Mount Static Files & Web Dashboard UI
static_dir = Path(__file__).resolve().parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Bulk Certificate Generator API is running. Visit /docs for OpenAPI documentation.",
        "docs_url": "/docs"
    }
