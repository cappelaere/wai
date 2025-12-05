"""
Configuration management for the copilot backend.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Server
    fastapi_host: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"

    # Claude API
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-4-1")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "2048"))

    # Paths
    processor_output_path: str = os.getenv("PROCESSOR_OUTPUT_PATH", "./output")
    application_data_path: str = os.getenv("APPLICATION_DATA_PATH", "./data")

    # Session
    session_timeout: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
    max_history: int = int(os.getenv("MAX_HISTORY", "100"))

    # CORS
    allowed_origins: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./copilot.db"
    )

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
