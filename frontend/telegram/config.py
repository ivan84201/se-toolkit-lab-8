"""Bot configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Resolve the .env file relative to the project root (two levels up from here)
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    BOT_TOKEN: str
    BACKEND_URL: str = Field(alias="TELEGRAM_BOT_BACKEND_URL")
    BACKEND_API_KEY: str = Field(alias="LMS_API_KEY")
    NANOBOT_API_URL: str = "http://nanobot:18790"
    LLM_API_MODEL: str = "coder-model"

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "populate_by_name": True,
        "extra": "ignore",
    }


def load_settings() -> Settings:
    return Settings()
