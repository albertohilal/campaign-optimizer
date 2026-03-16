"""Application configuration loaded from environment variables."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


# Load environment variables from .env if present
load_dotenv()


@dataclass(slots=True)
class Settings:
    """Centralized application settings."""

    app_name: str = os.getenv("APP_NAME", "Campaign Optimizer")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))

    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./campaign_optimizer.db",
    )

    # Google Ads credentials (used in Phase 2)
    google_ads_developer_token: str = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    google_ads_client_id: str = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
    google_ads_client_secret: str = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")
    google_ads_refresh_token: str = os.getenv("GOOGLE_ADS_REFRESH_TOKEN", "")
    google_ads_login_customer_id: str = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
    google_ads_customer_id: str = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")

    @property
    def is_development(self) -> bool:
        """Return True when the app runs in development mode."""
        return self.app_env.lower() == "development"

    @property
    def google_ads_credentials_present(self) -> bool:
        """Return True when all required Google Ads credentials are configured."""
        required_values = (
            self.google_ads_developer_token,
            self.google_ads_client_id,
            self.google_ads_client_secret,
            self.google_ads_refresh_token,
            self.google_ads_customer_id,
        )
        return all(value.strip() for value in required_values)

    @property
    def mock_google_ads_mode(self) -> bool:
        """
        Enable automatic mock mode in development when
        Google Ads credentials are missing.
        """
        return self.is_development and not self.google_ads_credentials_present


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()