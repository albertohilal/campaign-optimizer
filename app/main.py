"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import init_db
from app.logger import get_logger
from app.routes.analysis import router as analysis_router
from app.routes.campaigns import router as campaigns_router
from app.routes.health import router as health_router
from app.schemas import RootResponse


settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize application resources on startup and log shutdown."""

    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)
    logger.info("Mock Google Ads mode: %s", settings.mock_google_ads_mode)

    init_db()

    yield

    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(analysis_router)
app.include_router(campaigns_router)
app.include_router(health_router)


@app.get("/", response_model=RootResponse)
def root() -> RootResponse:
    """Return a simple service description for the current project phase."""

    return RootResponse(
        app_name=settings.app_name,
        message="Campaign Optimizer foundation is running.",
        phase="phase-1",
        docs_url="/docs",
        mock_mode_ready=settings.mock_google_ads_mode,
    )