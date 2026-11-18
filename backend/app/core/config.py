from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Pharmacy AI Support Platform"
    app_secret_key: str = "dev-change-me-before-production"
    api_prefix: str = "/api/v1"

    # Local Phase 1 default: SQLite. Production/Docker: PostgreSQL.
    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR / 'data' / 'pharmacy_ai.db'}"
    redis_url: str = "redis://localhost:6379/0"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    jwt_algorithm: str = "HS256"

    bootstrap_admin_email: str = "admin@pharmacy.uz"
    bootstrap_admin_password: str = "ChangeMeNow!123"
    bootstrap_admin_name: str = "Super Admin"

    rate_limit_auth_per_minute: int = 20
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_mode: str = "polling"  # polling | webhook | off

    upload_dir: str = str(ROOT_DIR / "data" / "uploads")
    max_upload_bytes: int = 15 * 1024 * 1024

    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"
    groq_vision_model: str = "qwen/qwen3.8-27b"
    groq_stt_model: str = "whisper-large-v3"

    # IT eskalatsiya telefonlari (vergul bilan). Faqat og'ir holatda ko'rsatiladi.
    escalation_phones: str = "+998971112233,+998901234567"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def escalation_phone_list(self) -> list[str]:
        return [p.strip() for p in self.escalation_phones.split(",") if p.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
