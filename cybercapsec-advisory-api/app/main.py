"""CyberCapSec Advisory API — FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    admin,
    assessments,
    auth,
    billing,
    evidence,
    guided_readiness,
    meta,
    policies,
    public,
    reports,
    roadmap,
    users,
)
from app.config import get_settings
from app.deps import require_paid_license

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown hooks."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered security and compliance advisory platform for African "
            "startups and SMEs. Generates regulatory roadmaps, control gap analysis, "
            "and continuous threat intelligence."
        ),
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    licensed_workspace = [Depends(require_paid_license)]
    app.include_router(meta.router, prefix=settings.API_V1_PREFIX)
    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(
        users.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        assessments.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        reports.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        policies.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        evidence.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        guided_readiness.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(
        roadmap.router,
        prefix=settings.API_V1_PREFIX,
        dependencies=licensed_workspace,
    )
    app.include_router(billing.router, prefix=settings.API_V1_PREFIX)
    app.include_router(public.router, prefix=settings.API_V1_PREFIX)
    app.include_router(admin.router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
