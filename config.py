import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False
    SECRET_KEY: str

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
    DB_ENCRYPTION_KEY: str

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = ""
    SMTP_USE_TLS: bool = True

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_PRO_ANNUAL_PRICE_ID: str = ""
    STRIPE_FAMILY_PLUS_PRICE_ID: str = ""
    STRIPE_FAMILY_PLUS_ANNUAL_PRICE_ID: str = ""
    STRIPE_SELF_HOSTED_PRICE_ID: str = ""

    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: str = ""
    SYNCO_LICENSE_KEY: str = ""
    SYNCO_LICENSE_SECRET: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"
    WEB_CONCURRENCY: int = 3
    SENTRY_DSN: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
