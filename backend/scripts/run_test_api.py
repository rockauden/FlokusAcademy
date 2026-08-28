"""Start an API instance against a disposable database, for end-to-end tests.

Playwright's webServer starts this. It builds a throwaway SQLite database by
running the real migration chain, seeds the two accounts, and serves the app --
so a test run never touches development or production data.

Environment is set before app.config is imported, because Settings reads it at
import time and refuses to start without SECRET_KEY.

Usage (normally only via playwright.config.js):
    python -m scripts.run_test_api [--port 8000]
"""
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Test-only credentials. These are not secrets: the database they unlock is
# created empty moments earlier and deleted when the run ends.
TEST_ENV = {
    "SECRET_KEY": "e2e-test-key-not-a-secret-0123456789abcdef",
    "ADMIN_PIN": "1234",
    "STUDENT_PIN": "4321",
    # Tests run over plain http on localhost, where a Secure cookie is dropped.
    "COOKIE_SECURE": "false",
    "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174",
    # The suite signs in repeatedly from one address; the production limit of
    # 5/minute would throttle the run itself rather than test anything.
    "LOGIN_RATE_LIMIT": "1000/minute",
    "REFRESH_RATE_LIMIT": "1000/minute",
    # Not a working key, and deliberately so. It is only here to get past the
    # "AI tutor disabled" guard so the safety layer can be exercised -- that
    # path short-circuits before any model call, so no request ever leaves the
    # machine and no real key is needed to test the thing that matters most.
    "GEMINI_API_KEY": "e2e-placeholder-not-a-real-key",
    # Production ships with the tutor OFF (see FLOKI_ENABLED in app/config.py).
    # The suite turns it on because the safety and stuck-flag specs are the most
    # important tests in the repo and only run when the feature is reachable.
    # The switched-off experience is covered from the client side in
    # floki.spec.js, which intercepts the status call rather than restarting the
    # API with a different environment.
    "FLOKI_ENABLED": "true",
}


def _prepare_database() -> Path:
    """Create an empty database and bring it to head with the real chain."""
    db_path = Path(tempfile.mkdtemp(prefix="flokus-e2e-")) / "e2e.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path.as_posix()}"

    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")

    return db_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    for key, value in TEST_ENV.items():
        os.environ.setdefault(key, value)

    db_path = _prepare_database()

    import asyncio

    from app.seed import main as seed_main

    seed_result = seed_main()
    if asyncio.iscoroutine(seed_result):
        asyncio.run(seed_result)

    import uvicorn

    print(f"e2e API on :{args.port}, database {db_path}", flush=True)
    try:
        # Bind the hostname rather than 127.0.0.1: on Windows, Node resolves
        # "localhost" to ::1 first, and an IPv4-only bind leaves the vite proxy
        # unable to connect.
        uvicorn.run("app.main:app", host="localhost", port=args.port, log_level="warning")
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
