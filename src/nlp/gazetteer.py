"""Cricket Entity Gazetteer & Canonical Registry.

Loads verified entity aliases from configuration and syncs with SQLite database
canonical tables (teams, players, matches, venues), tracking ambiguity and boundary patterns.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from src.nlp.schemas import EntityType
from src.storage.sqlite_manager import SQLiteStorageManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GazetteerEntry:
    """An individual audited entity alias entry."""
    alias_text: str
    canonical_id: str
    entity_type: EntityType
    is_ambiguous: bool = False
    primary_team_id: Optional[str] = None
    notes: str = ""
    source: str = "seed_gazetteer"


class CricketGazetteer:
    """Auditable entity registry providing boundary-aware matching and alias lookup."""

    def __init__(
        self,
        config_path: Optional[str | Path] = None,
        storage: Optional[SQLiteStorageManager] = None,
    ):
        self.config_path = Path(config_path) if config_path else Path("config/cricket_gazetteer.yaml")
        self.storage = storage
        self.version = "1.0.0"
        self._entries_by_alias: Dict[str, List[GazetteerEntry]] = {}
        self._canonical_names: Dict[str, str] = {}
        self._compiled_regex: Optional[re.Pattern] = None

        self._load_from_yaml()
        if self.storage:
            self._sync_with_storage()
        self._compile_patterns()

    def _load_from_yaml(self) -> None:
        """Loads audited seed entity aliases from YAML."""
        if not self.config_path.exists():
            logger.warning(f"Gazetteer config not found at {self.config_path}, initializing empty")
            return

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self.version = data.get("version", "1.0.0")
        entities_data = data.get("entities", {})

        # 1. Teams
        for team in entities_data.get("teams", []):
            cid = team["canonical_id"]
            name = team["name"]
            self._canonical_names[cid] = name
            for alias in team.get("aliases", []):
                entry = GazetteerEntry(
                    alias_text=alias["text"],
                    canonical_id=cid,
                    entity_type=EntityType.TEAM,
                    is_ambiguous=alias.get("ambiguous", False),
                    notes=alias.get("notes", ""),
                    source="yaml_seed",
                )
                self._add_entry(entry)

        # 2. Players
        for player in entities_data.get("players", []):
            cid = player["canonical_id"]
            name = player["full_name"]
            team_id = player.get("primary_team_id")
            self._canonical_names[cid] = name
            for alias in player.get("aliases", []):
                entry = GazetteerEntry(
                    alias_text=alias["text"],
                    canonical_id=cid,
                    entity_type=EntityType.PLAYER,
                    is_ambiguous=alias.get("ambiguous", False),
                    primary_team_id=team_id,
                    notes=alias.get("notes", ""),
                    source="yaml_seed",
                )
                self._add_entry(entry)

        # 3. Tournaments
        for tourn in entities_data.get("tournaments", []):
            cid = tourn["canonical_id"]
            name = tourn["name"]
            self._canonical_names[cid] = name
            for alias in tourn.get("aliases", []):
                entry = GazetteerEntry(
                    alias_text=alias["text"],
                    canonical_id=cid,
                    entity_type=EntityType.TOURNAMENT,
                    is_ambiguous=alias.get("ambiguous", False),
                    notes=alias.get("notes", ""),
                    source="yaml_seed",
                )
                self._add_entry(entry)

        # 4. Venues
        for venue in entities_data.get("venues", []):
            cid = venue["canonical_id"]
            name = venue["name"]
            self._canonical_names[cid] = name
            for alias in venue.get("aliases", []):
                entry = GazetteerEntry(
                    alias_text=alias["text"],
                    canonical_id=cid,
                    entity_type=EntityType.VENUE,
                    is_ambiguous=alias.get("ambiguous", False),
                    notes=alias.get("notes", ""),
                    source="yaml_seed",
                )
                self._add_entry(entry)

    def _sync_with_storage(self) -> None:
        """Enriches the gazetteer with canonical records from SQLite."""
        if not self.storage:
            return

        with self.storage._get_connection() as conn:
            cursor = conn.cursor()
            # Sync teams
            cursor.execute("SELECT team_id, name, aliases_json FROM teams;")
            for row in cursor.fetchall():
                tid = row["team_id"]
                name = row["name"]
                self._canonical_names[tid] = name
                self._add_entry(GazetteerEntry(alias_text=name, canonical_id=tid, entity_type=EntityType.TEAM, source="db_sync"))
                self._add_entry(GazetteerEntry(alias_text=tid, canonical_id=tid, entity_type=EntityType.TEAM, source="db_sync"))
                try:
                    aliases = json.loads(row["aliases_json"] or "[]")
                    for a in aliases:
                        self._add_entry(GazetteerEntry(alias_text=a, canonical_id=tid, entity_type=EntityType.TEAM, source="db_sync"))
                except Exception:
                    pass

            # Sync players
            cursor.execute("SELECT player_id, full_name, primary_team_id, aliases_json FROM players;")
            for row in cursor.fetchall():
                pid = row["player_id"]
                name = row["full_name"]
                team_id = row["primary_team_id"]
                self._canonical_names[pid] = name
                self._add_entry(GazetteerEntry(alias_text=name, canonical_id=pid, entity_type=EntityType.PLAYER, primary_team_id=team_id, source="db_sync"))
                try:
                    aliases = json.loads(row["aliases_json"] or "[]")
                    for a in aliases:
                        self._add_entry(GazetteerEntry(alias_text=a, canonical_id=pid, entity_type=EntityType.PLAYER, primary_team_id=team_id, source="db_sync"))
                except Exception:
                    pass

    def _add_entry(self, entry: GazetteerEntry) -> None:
        """Registers an entry in the alias index."""
        key = entry.alias_text.strip().lower()
        if not key:
            return
        if key not in self._entries_by_alias:
            self._entries_by_alias[key] = []
        # Check if already present
        if not any(e.canonical_id == entry.canonical_id and e.alias_text == entry.alias_text for e in self._entries_by_alias[key]):
            self._entries_by_alias[key].append(entry)

    def _compile_patterns(self) -> None:
        """Compiles boundary-aware regular expression matching longest aliases first."""
        aliases = list(self._entries_by_alias.keys())
        if not aliases:
            self._compiled_regex = None
            return

        # Sort by length descending so longer phrases match first (e.g. "West Indies" before "Indies")
        aliases.sort(key=len, reverse=True)
        # Escape each alias, enforce word boundaries (\b)
        patterns = []
        for a in aliases:
            # Handle special characters or standard boundary
            patterns.append(rf"\b{re.escape(a)}\b")

        master_regex = r"|".join(patterns)
        self._compiled_regex = re.compile(rf"({master_regex})", re.IGNORECASE)

    def lookup_alias(self, surface_text: str) -> List[GazetteerEntry]:
        """Returns all registered gazetteer entries for a surface string."""
        return self._entries_by_alias.get(surface_text.strip().lower(), [])

    def get_canonical_name(self, canonical_id: str) -> str:
        """Retrieves official full display name for a canonical ID."""
        return self._canonical_names.get(canonical_id, canonical_id)

    def find_matches(self, text: str) -> List[tuple[int, int, str, List[GazetteerEntry]]]:
        """
        Scans text for all boundary-matched gazetteer entities.
        Returns list of tuples: (start_char, end_char, surface_text, entries)
        """
        if not self._compiled_regex or not text:
            return []

        results = []
        for m in self._compiled_regex.finditer(text):
            surface = m.group(0)
            entries = self.lookup_alias(surface)
            if entries:
                results.append((m.start(), m.end(), surface, entries))

        return results
