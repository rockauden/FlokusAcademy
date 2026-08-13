import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, async_session_maker
from app.services.curriculum_seeder import seed_initial_data

from app.routers import auth, courses, modules, tasks, schedule, events, expenses, projects, analytics, ai_tutor, rewards

app = FastAPI(
    title="Flokus Academy API",
    description="Backend for the Flokus Academy Homeschool LMS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    await init_db()
    async with async_session_maker() as session:
        await seed_initial_data(session)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
