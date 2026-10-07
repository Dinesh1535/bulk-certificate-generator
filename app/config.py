from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    APP_NAME: str = "Bulk Certificate Generator"
    APP_ENV: str = "development"
    DEBUG: bool = True
    VERSION: str = "1.0.0"

    # Base directory of the project
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Storage paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    CERTIFICATES_DIR: Path = STORAGE_DIR / "certificates"
    ZIPS_DIR: Path = STORAGE_DIR / "zips"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'certificates.db'}"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Max bulk recipients per single request
    MAX_RECIPIENTS_PER_BATCH: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_storage(self) -> None:
        """Ensure all required storage directories exist."""
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
        self.ZIPS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_storage()
