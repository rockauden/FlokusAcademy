from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://localhost/flokus"

    # Required. The application refuses to start without these — a fallback
    # value here would silently sign production tokens with a key that is
    # public in the repository.
    #
    # SecretStr keeps the values out of reprs and out of pydantic's
    # ValidationError output, so a failed boot cannot write them to the logs.
    # Read them with .get_secret_value().
    SECRET_KEY: SecretStr
    ADMIN_PIN: SecretStr
    STUDENT_PIN: SecretStr

    GEMINI_API_KEY: SecretStr | None = None

    # Comma-separated list of allowed browser origins, e.g.
    # "https://flokus.app,https://www.flokus.app". Read via cors_origin_list.
    CORS_ORIGINS: str = "http://localhost:5173"

    # Long enough to cover a continuous morning of coursework without bouncing
    # a child to the login screen mid-lesson, short enough to force a daily
    # re-auth. Immediate revocation is handled by the is_active check in
    # get_current_active_user, not by the expiry.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 240

    # Refresh tokens live in an HttpOnly cookie and are rotated on every use.
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Secure cookies require HTTPS. Set false for plain-http local development.
    COOKIE_SECURE: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def _reject_weak_secret_key(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        # SecretStr only redacts reprs. Pydantic still echoes the raw input
        # into ValidationError output, which on a failed boot would write the
        # whole environment — API keys included — to the deploy logs.
        hide_input_in_errors = True

settings = Settings()
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif settings.DATABASE_URL.startswith("postgresql://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
