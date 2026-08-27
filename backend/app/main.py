import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_maker, engine, get_db
from app.observability import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
    configure_logging,
    get_request_id,
)
from app.rate_limit import limiter
from app.services.retention import purge_old_chat_history

configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)

from app.routers import auth, courses, maintenance, modules, tasks, week, schedule, events, expenses, projects, analytics, ai_tutor, rewards, students, app_config

logger = logging.getLogger(__name__)


async def _safe_rollback(session: AsyncSession) -> None:
    """Roll back without ever raising.

    Used only by the readiness probe. A rollback against a connection that has
    already dropped can itself fail, and that would turn a deliberate 503 into
    a 500 — losing exactly the diagnostic the endpoint exists to provide. This
    is verified on SQLite locally; the failure mode it guards against is a
    Postgres one, so it fails safe rather than relying on the local result.
    """
    try:
        await session.rollback()
    except Exception:
        logger.debug("Rollback during readiness check failed", exc_info=True)


async def _run_retention_purge() -> None:
    """Best-effort. Retention must never be the reason the API fails to serve."""
    try:
        async with asyncio.timeout(60):
            async with async_session_maker() as session:
                await purge_old_chat_history(session)
    except Exception:
        logger.exception("Retention purge failed; continuing without it")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Scheduled rather than awaited: startup completes immediately and the
    # purge runs alongside the first requests. A slow or unreachable database
    # delays cleanup, it does not delay the app coming up.
    task = asyncio.create_task(_run_retention_purge())
    yield
    if not task.done():
        task.cancel()
    # Drain the pool so in-flight queries are not cut mid-deploy.
    await engine.dispose()


app = FastAPI(
    title="Flokus Academy API",
    description="Backend for the Flokus Academy Homeschool LMS",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Turn an unhandled error into a logged, quotable 500.

    The exception itself goes to the logs with the request id attached; the
    caller gets that id and nothing else. Exception text routinely contains
    connection strings, query fragments and internal paths, none of which
    belong on a nine-year-old's screen or in a browser's network tab.
    """
    request_id = get_request_id()
    logger.exception(
        "Unhandled error on %s %s (request_id=%s)",
        request.method, request.url.path, request_id,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong on our end. Please try again.",
            "request_id": request_id,
        },
        headers={REQUEST_ID_HEADER: request_id},
    )


# Added last so it runs first: the id must exist before anything else can log.
app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
    # Without this the browser cannot read the header, so a request id shown to
    # the user would be invisible to the code that needs to display it.
    expose_headers=[REQUEST_ID_HEADER],
)

# Include Routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(modules.router)
app.include_router(tasks.router)
app.include_router(week.router)
app.include_router(maintenance.router)
app.include_router(schedule.router)
app.include_router(events.router)
app.include_router(expenses.router)
app.include_router(projects.router)
app.include_router(analytics.router)
app.include_router(ai_tutor.router)
app.include_router(rewards.router)
app.include_router(students.router)
app.include_router(app_config.router)

@app.get("/health")
async def health_check():
    """Liveness. Deliberately does not touch the database.

    railway.toml points healthcheckPath here with restartPolicyType =
    "on_failure", so this has to stay a static literal: if it queried Postgres,
    a transient connection blip would restart an otherwise healthy container
    and turn a brief database hiccup into a crash loop. "Is the process
    serving?" and "can it reach its dependencies?" are different questions with
    different correct responses, which is why readiness is a separate endpoint.
    """
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check(response: Response, db: AsyncSession = Depends(get_db)):
    """Readiness — can this instance actually serve a request that needs data?

    Also reports the applied Alembic revision. That is the useful part: it
    makes migration state checkable from outside without shell access to the
    database, which is exactly the gap that let production drift from the
    migration chain unnoticed once already.

    Returns 503 with a reason rather than raising, so a probe (or a human with
    curl) gets the failure mode in the body instead of a bare 500.
    """
    # The two checks are deliberately separate. "Cannot reach the database" and
    # "reached it but it has no migration state" are different failures with
    # different fixes, and reporting them identically would have made the
    # production schema drift harder to spot, not easier.
    #
    # Exception detail is the class name only: the full text can carry the
    # connection string, credentials included, and this endpoint is public.
    try:
        # A hung database must not hang the probe — an unbounded wait here
        # would make the readiness check itself a source of downtime.
        async with asyncio.timeout(5):
            await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Readiness check failed: database unreachable")
        await _safe_rollback(db)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unavailable",
            "database": "error",
            "detail": type(exc).__name__,
        }

    try:
        async with asyncio.timeout(5):
            revision = (
                await db.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one_or_none()
    except Exception as exc:
        # The table is absent: this database was never migrated. Distinct from
        # the branch below, where the table exists but holds no row.
        logger.exception("Readiness check failed: migration state unreadable")
        await _safe_rollback(db)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unavailable",
            "database": "ok",
            "migration": "unreadable",
            "detail": type(exc).__name__,
        }

    if revision is None:
        # Table present but empty — Alembic has never stamped it. A database in
        # this state fails in confusing ways later, so it is not "ready".
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "ok", "migration": None}

    return {"status": "ready", "database": "ok", "migration": revision}
