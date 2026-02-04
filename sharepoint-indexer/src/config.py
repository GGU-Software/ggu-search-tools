"""
Configuration module for GGU TechDoc Search.

Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Azure AD App Registration
    sharepoint_client_id: str
    sharepoint_client_secret: str
    sharepoint_tenant_id: str

    # SharePoint Configuration
    sharepoint_host: str = "ggu.sharepoint.de"
    sharepoint_site: str = "sites/GGUTeamSite"
    sharepoint_drive: str = "GGU"
    sharepoint_folder: str = "Bibliothek"

    # Pinecone Assistant
    pinecone_api_key: Optional[str] = None
    pinecone_assistant_name: str = "ggu-techdoc-search"

    # Sync State
    state_db_path: str = "state.db"

    # Processing
    supported_extensions: list[str] = [".pdf"]
    max_folder_depth: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
