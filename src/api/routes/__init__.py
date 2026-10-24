"""API Route Registrations and Aggregator."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.analytics import router as analytics_router
from src.api.routes.articles import router as articles_router
from src.api.routes.commentary import router as commentary_router
from src.api.routes.health import router as health_router
from src.api.routes.matches import router as matches_router
from src.api.routes.nlp import router as nlp_router
from src.api.routes.observability import router as observability_router
from src.api.routes.players import router as players_router
from src.api.routes.teams import router as teams_router

# Version 1 API router: all endpoints grouped under /api/v1
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(matches_router)
api_v1_router.include_router(players_router)
api_v1_router.include_router(teams_router)
api_v1_router.include_router(articles_router)
api_v1_router.include_router(commentary_router)
api_v1_router.include_router(nlp_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(observability_router)

__all__ = [
    "health_router",
    "api_v1_router",
    "matches_router",
    "players_router",
    "teams_router",
    "articles_router",
    "commentary_router",
    "nlp_router",
    "analytics_router",
    "observability_router",
]
