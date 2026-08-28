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

    # Rate limits, in slowapi's syntax. Tunable per environment because the
    # end-to-end suite signs in many times in quick succession from a single
    # address and would otherwise throttle itself. The defaults are the
    # production values — nothing has to be set for those to apply.
    LOGIN_RATE_LIMIT: str = "5/minute"
    REFRESH_RATE_LIMIT: str = "30/minute"

    # Logging. Set LOG_FORMAT=json in production so the platform can index the
    # fields; plain text is far easier to read in a local terminal.
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"

    # Ask Floki guardrails.
    #
    # A per-day ceiling on messages, per student. This is a cost and abuse
    # bound, not a teaching limit -- it sits well above a normal school day's
    # use, and is there so a stuck loop or a bored afternoon cannot run up an
    # unbounded bill against the Gemini key.
    FLOKI_DAILY_MESSAGE_LIMIT: int = 60

    # How many past messages are replayed as context. The implementation used
    # to send the entire session every turn, so cost grew with the square of
    # the conversation length and would eventually exceed the context window
    # outright. A rolling window keeps both bounded.
    FLOKI_CONTEXT_MESSAGES: int = 20

    # Master switch for Ask Floki, and it defaults to OFF on purpose.
    #
    # Google's Gemini API Additional Terms say an API Client must not be
    # "directed towards or ... likely to be accessed by individuals under the
    # age of 18", and on the unpaid tier Google uses submitted prompts to train
    # its models, with human reviewers able to read them. This application is
    # used by one nine-year-old, so both clauses bite.
    #
    # Off by default means a fresh deploy, a new environment or a forgotten
    # variable all fail in the safe direction: the tutor is simply absent.
    # Turning it on is a deliberate act that should follow a paid API key (or a
    # provider whose terms permit under-18 use with parental consent) -- not a
    # default someone inherits without knowing what it sends where.
    #
    # Nothing else is removed when this is false. Transcripts, safety events,
    # consent records and retention all keep working, so the feature comes back
    # by flipping one variable rather than by rebuilding it.
    FLOKI_ENABLED: bool = False

    # Secure cookies require HTTPS. Set false for plain-http local development.
    COOKIE_SECURE: bool = True

    # Swagger UI, ReDoc and the OpenAPI schema. Off by default.
    #
    # These were reachable unauthenticated in production, which handed anyone
    # who found the hostname a complete, machine-readable map of every endpoint
    # -- including the destructive maintenance route and the login shape. None
    # of that is secret exactly, but publishing it to strangers buys nothing
    # when the only two users are a father and his son, and the source is right
    # here for anyone who is meant to have it.
    #
    # Set ENABLE_API_DOCS=true locally when exploring the API by hand.
    ENABLE_API_DOCS: bool = False

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
