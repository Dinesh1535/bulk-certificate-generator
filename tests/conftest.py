import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
import app.database as app_db
import app.services.job_processor as app_job_processor
from app.main import app

# Temporary test directory
TEST_DIR = Path(tempfile.mkdtemp(prefix="test_cert_gen_"))
TEST_DB_PATH = TEST_DIR / "test.db"
TEST_STORAGE = TEST_DIR / "storage"
TEST_CERTS_DIR = TEST_STORAGE / "certificates"
TEST_ZIPS_DIR = TEST_STORAGE / "zips"

TEST_CERTS_DIR.mkdir(parents=True, exist_ok=True)
TEST_ZIPS_DIR.mkdir(parents=True, exist_ok=True)

# Patch settings paths to temporary test directory
settings.STORAGE_DIR = TEST_STORAGE
settings.CERTIFICATES_DIR = TEST_CERTS_DIR
settings.ZIPS_DIR = TEST_ZIPS_DIR
settings.DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Rebind SessionLocal across database and job processor modules for testing
app_db.SessionLocal = TestingSessionLocal
app_db.engine = test_engine
app_job_processor.SessionLocal = TestingSessionLocal


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[app_db.get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    app_db.Base.metadata.create_all(bind=test_engine)
    yield
    app_db.Base.metadata.drop_all(bind=test_engine)
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR, ignore_errors=True)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
