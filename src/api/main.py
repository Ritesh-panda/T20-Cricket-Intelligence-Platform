"""FastAPI Application Entry Point for T20 Cricket Intelligence Platform.

Provides documented REST APIs for research, media attention analytics,
cricket performance data, NLP narrative intelligence, and APDI metrics.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import settings
from src.api.errors import register_error_handlers
from src.api.routes import api_v1_router, health_router
from src.storage.sqlite_manager import SQLiteStorageManager

# Configure API logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api_main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle: persistence initialization and teardown."""
    logger.info("Initializing API application persistence...")
    storage = SQLiteStorageManager(settings.db_path)
    app.state.storage = storage
    logger.info(f"SQLite persistence bound to database: {settings.db_path}")

    yield

    logger.info("Shutting down API application...")


def create_app() -> FastAPI:
    """Creates and configures a production-ready FastAPI application instance."""
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )

    # 1. Restrictive CORS configuration
    cors_origins = (
        settings.cors_origins
        if isinstance(settings.cors_origins, list)
        else [settings.cors_origins]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # 2. Safe standardized error handlers
    register_error_handlers(app)

    # 3. Mount routes
    app.include_router(health_router)
    app.include_router(api_v1_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
