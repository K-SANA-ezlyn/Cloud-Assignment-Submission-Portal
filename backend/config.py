"""
config.py — Central configuration (12-Factor App style).

Every setting comes from environment variables (or a local `.env` file).
NO secret is ever hardcoded here. This is a core cloud-native practice:
the same container/image can be promoted from local -> staging -> cloud
by changing only the environment.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime settings, validated at startup by pydantic."""

    model_config = SettingsConfigDict(
        env_file=".env",          # local development convenience
        env_file_encoding="utf-8",
        extra="ignore",           # ignore unrelated env vars on cloud hosts
    )

    # ----- Application -----
    APP_NAME: str = "Cloud Assignment Submission Portal"
    ENVIRONMENT: str = "local"          # local | cloud
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ----- Security -----
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # ----- Roles -----
    TEACHER_INVITE_CODE: str = "TEACHER-2026-DEMO"

    # ----- Demo seeder (dummy accounts; override via env) -----
    SEED_TEACHER_PASSWORD: str = "Teacher@12345"
    SEED_STUDENT_PASSWORD: str = "Student@12345"

    # ----- Cloud abstraction: database -----
    DATABASE_URL: str = "sqlite:///./portal.db"

    # ----- Cloud abstraction: object storage -----
    STORAGE_PROVIDER: str = "local"     # local | supabase
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10

    # ----- Cloud abstraction: authentication provider -----
    AUTH_PROVIDER: str = "local"        # local | supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "submissions"

    # ----- Networking -----
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # ----- Derived helpers -----
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def is_local_mode(self) -> bool:
        """True when the whole system runs on the local machine."""
        return self.ENVIRONMENT == "local"


@lru_cache
def get_settings() -> Settings:
    """Cache settings so the .env file is parsed only once per process."""
    return Settings()


settings = get_settings()
