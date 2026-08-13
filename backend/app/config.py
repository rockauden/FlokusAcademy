from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://localhost/flokus"
    SECRET_KEY: str = "dev_secret_key_123456789"
    GEMINI_API_KEY: str | None = None
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    ADMIN_PIN: str = "1234"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"

settings = Settings()
