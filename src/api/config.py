"""API Configuration & Settings for T20 Cricket Intelligence Platform.

Manages environment-backed configuration for the FastAPI service, including
database paths, CORS policies, pagination defaults, and API versioning.
"""

from __future__ import annotations

import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Configuration settings for FastAPI research backend."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_title: str = "T20 Cricket Intelligence Platform Research API"
    api_description: str = (
        "Open-source research API exposing canonical match records, editorial media attention "
        "metrics, objective cricket performance statistics, narrative framing analysis, and the "
        "Attention-to-Performance Discrepancy Index (APDI)."
    )
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # Database & Storage
    db_path: str = Field(default="data/cricket_intel.db", description="Path to SQLite database")
    default_tournament: str = "T20 World Cup 2024"

    # CORS Configuration (never allow credentials with wildcard)
    cors_origins: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origin list for local web dashboard clients",
    )
    cors_allow_credentials: bool = False
    cors_allow_methods: List[str] = ["GET", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Pagination Defaults
    default_page_limit: int = 20
    max_page_limit: int = 100

    debug: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = APISettings()
