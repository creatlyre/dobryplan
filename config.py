import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"

    SUPABASE_URL: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "")
        or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    )
    SUPABASE_ANON_KEY: str = Field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "")
        or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY", "")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    )
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"
    GOOGLE_SCOPES: List[str] = Field(
        default_factory=lambda: [
            "openid",
            "profile",
            "email",
            "https://www.googleapis.com/auth/calendar",
        ]
    )
    GOOGLE_EVENT_REMINDER_MINUTES: int = 30

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 8
    DB_ENCRYPTION_KEY: str = "your-encryption-key-for-oauth-tokens"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
