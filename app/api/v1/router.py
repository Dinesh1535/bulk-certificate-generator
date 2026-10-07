from fastapi import APIRouter
from app.api.v1.jobs import router as jobs_router
from app.api.v1.certificates import router as certificates_router

api_router = APIRouter(prefix="/v1")

@api_router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "Bulk Certificate Generator API",
        "version": "1.0.0"
    }

api_router.include_router(jobs_router)
api_router.include_router(certificates_router)
