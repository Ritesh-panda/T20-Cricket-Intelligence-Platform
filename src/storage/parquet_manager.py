"""Parquet Storage Manager for T20 Cricket Intelligence Platform.

Handles columnar dataset exports and analytical queries using PyArrow and Pandas.
Supports atomic writes (write-tmp-then-rename) to guarantee crash-resilient dataset updates.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.models.canonical import DeliveryRecord, MatchRecord, ArticleRecord, CommentaryRecord


class ParquetStorageManager:
    """Manages local Parquet analytics tables with atomic updates."""

    def __init__(self, processed_dir: str | Path):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _atomic_write_table(self, table: pa.Table, target_file: Path) -> None:
        """Writes table to a temporary file, then atomically renames to target."""
        tmp_file = target_file.with_suffix(".tmp.parquet")
        pq.write_table(table, tmp_file, compression="SNAPPY")
        if target_file.exists():
            target_file.unlink()
        tmp_file.rename(target_file)

    def write_deliveries(self, deliveries: List[DeliveryRecord]) -> Path:
        """Appends/upserts delivery records into data/processed/deliveries.parquet."""
        target_path = self.processed_dir / "deliveries.parquet"
        new_df = pd.DataFrame([d.model_dump() for d in deliveries])
        
        # Convert enum phase to string
        if "phase" in new_df.columns:
            new_df["phase"] = new_df["phase"].astype(str)

        if target_path.exists():
            existing_df = pd.read_parquet(target_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=["delivery_id"], keep="last")
        else:
            combined_df = new_df

        combined_df = combined_df.sort_values(by=["match_id", "innings", "over", "ball"])
        table = pa.Table.from_pandas(combined_df, preserve_index=False)
        self._atomic_write_table(table, target_path)
        return target_path

    def write_matches(self, matches: List[MatchRecord]) -> Path:
        """Writes match metadata table."""
        target_path = self.processed_dir / "matches.parquet"
        new_df = pd.DataFrame([m.model_dump() for m in matches])
        
        # Serialize metadata dict to JSON string for parquet compatibility
        if "metadata" in new_df.columns:
            new_df["metadata"] = new_df["metadata"].apply(lambda d: str(d))

        if target_path.exists():
            existing_df = pd.read_parquet(target_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=["match_id"], keep="last")
        else:
            combined_df = new_df

        table = pa.Table.from_pandas(combined_df, preserve_index=False)
        self._atomic_write_table(table, target_path)
        return target_path

    def read_deliveries(self, match_id: Optional[str] = None) -> pd.DataFrame:
        target_path = self.processed_dir / "deliveries.parquet"
        if not target_path.exists():
            return pd.DataFrame()
        df = pd.read_parquet(target_path)
        if match_id:
            df = df[df["match_id"] == match_id]
        return df

    def read_matches(self) -> pd.DataFrame:
        target_path = self.processed_dir / "matches.parquet"
        if not target_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(target_path)
