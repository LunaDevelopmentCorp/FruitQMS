"""FruitQMS FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database.engine import engine
from src.models.base import Base

# Import ALL models so Base.metadata.create_all picks up every table
import src.models.auth  # noqa: F401
import src.models.organization  # noqa: F401
import src.models.qms_forms  # noqa: F401
import src.models.qms_operations  # noqa: F401
import src.models.qms_integrations  # noqa: F401
import src.models.audit  # noqa: F401
import src.models.standards  # noqa: F401  (Phase 2 — models only, no routes yet)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    import asyncio
    from src.services.fruitpak_poller import poll_fruitpak_batches

    # Startup: create all tables (dev only — use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start FruitPak background poller (no-op if not configured)
    poller_task = asyncio.create_task(poll_fruitpak_batches())

    yield

    # Shutdown: cancel poller and dispose engine
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Quality Management System for fruit packhouses",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


# Import and register routers (will be added as we build each step)
from src.api.v1.auth import router as auth_router
from src.api.v1.organization import router as org_router
from src.api.v1.qms_forms import router as forms_router
from src.api.v1.qms_operations import router as qms_ops_router
from src.api.v1.qms_reports import router as reports_router
from src.api.v1.i18n import router as i18n_router
from src.api.v1.fruitpak import router as fruitpak_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(org_router, prefix="/api/v1", tags=["Organizations"])
app.include_router(forms_router, prefix="/api/v1/forms", tags=["Form Engine"])
app.include_router(qms_ops_router, prefix="/api/v1/qms", tags=["QMS Operations"])
app.include_router(reports_router, prefix="/api/v1/qms/reports", tags=["QMS Reports"])
app.include_router(i18n_router, prefix="/api/v1/i18n", tags=["Internationalization"])
app.include_router(fruitpak_router, prefix="/api/v1/fruitpak", tags=["FruitPak Integration"])
