"""FastAPI Research and Analytics API Package."""

from __future__ import annotations

from src.api.config import settings
from src.api.main import app, create_app

__all__ = ["app", "create_app", "settings"]
