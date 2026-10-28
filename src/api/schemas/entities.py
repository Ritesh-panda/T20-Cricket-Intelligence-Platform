"""Pydantic Models for Canonical Players and Teams."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class PlayerResponse(BaseModel):
    """Canonical player identity record."""
    player_id: str
    full_name: str
    cricsheet_id: Optional[str] = None
    primary_team_id: Optional[str] = None
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    role: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)


class TeamResponse(BaseModel):
    """Canonical team identity record."""
    team_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
