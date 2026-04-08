# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging


# Configure logging
# Trigger reload
from backend.logging_config import setup_logging
logger = setup_logging()

from backend.auth import router as auth_router
from backend.routers.users import router as users_router
from backend.routers.tasks import router as tasks_router
from backend.routers.admin import router as admin_router
from backend.routers.tools import router as tools_router
from backend.routers.files import router as files_router
from backend.routers.rag import router as rag_router, rag_meta_router

from contextlib import asynccontextmanager
import asyncio
from backend.database import init_db
# Import models to register for init_db
from backend.retrieval.models import UserCollection
from backend.models.telemetry import TelemetrySnapshot  # noqa: F401 — registers table with SQLModel
from backend.agents.preload_manager import preload_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Start model preloading in background (non-blocking)
    asyncio.create_task(preload_manager.startup_preload())
    logger.info("Model preload task started in background")
    yield

app = FastAPI(title="Mentori Backend (Minimal)", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tasks_router)
app.include_router(admin_router)
app.include_router(tools_router)
app.include_router(files_router)
app.include_router(rag_router)
app.include_router(rag_meta_router)
from backend.routers.system import router as system_router
app.include_router(system_router)

from fastapi.staticfiles import StaticFiles
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")

# Middleware - CORS configuration
# Build allowed origins from environment variable + defaults
cors_origins = ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"]
frontend_origin = os.environ.get("FRONTEND_ORIGIN")
if frontend_origin and frontend_origin not in cors_origins:
    cors_origins.append(frontend_origin)
    logger.info(f"Added CORS origin from FRONTEND_ORIGIN: {frontend_origin}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Mentori Backend", "version": "Minimal 1.0"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting minimal backend server...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8766, reload=True)
