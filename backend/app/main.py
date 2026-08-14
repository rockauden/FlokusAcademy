import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import async_session_maker, engine
from app.rate_limit import limiter
from app.services.retention import purge_old_chat_history

from app.routers import auth, courses, modules, tasks, schedule, events, expenses, projects, analytics, ai_tutor, rewards, students

logger = logging.getLogger(__name__)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(modules.router)
app.include_router(tasks.router)
app.include_router(schedule.router)
app.include_router(events.router)
app.include_router(expenses.router)
app.include_router(projects.router)
app.include_router(analytics.router)
app.include_router(ai_tutor.router)
app.include_router(rewards.router)
app.include_router(students.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
