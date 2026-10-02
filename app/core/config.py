import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

class Settings(BaseModel):
    whatsapp_access_token: str = Field(default_factory=lambda: os.getenv("WHATSAPP_ACCESS_TOKEN", ""))
    whatsapp_phone_number_id: str = Field(default_factory=lambda: os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""))
    whatsapp_verify_token: str = Field(default_factory=lambda: os.getenv("WHATSAPP_VERIFY_TOKEN", "change-me"))
    whatsapp_api_version: str = Field(default_factory=lambda: os.getenv("WHATSAPP_API_VERSION", "v23.0"))
    meta_app_secret: str = Field(default_factory=lambda: os.getenv("META_APP_SECRET", ""))
    supabase_url: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = Field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    admin_api_key: str = Field(default_factory=lambda: os.getenv("ADMIN_API_KEY", "change-me"))
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = Field(default_factory=lambda: _bool("DEBUG", True))
    demo_mode: bool = Field(default_factory=lambda: _bool("DEMO_MODE", True))
    require_webhook_signature: bool = Field(default_factory=lambda: _bool("REQUIRE_WEBHOOK_SIGNATURE", False))
    local_database_path: str = Field(default_factory=lambda: os.getenv("LOCAL_DATABASE_PATH", "whatsapp_demo.db"))

    @property
    def signature_required(self) -> bool:
        return self.environment.lower() == "production" or self.require_webhook_signature

@lru_cache
def get_settings() -> Settings:
    return Settings()

