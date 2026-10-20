"""
Orchestrator for text embedding generation, caching, and persistence.
"""

import hashlib
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import numpy as np

from src.analysis.analysis_schemas import EmbeddingMetadataRecord
from src.analysis.embedding_models import BaseEmbeddingModel, get_embedding_model

if TYPE_CHECKING:
    from src.storage.sqlite_manager import SQLiteStorageManager


class EmbeddingPipeline:
    """
    Manages embedding generation for normalized records with caching and idempotency.
    """

    def __init__(
        self,
        storage: Optional["SQLiteStorageManager"] = None,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        vector_storage_dir: str = "data/processed/embeddings",
    ):
        self.storage = storage
        self.model = embedding_model or get_embedding_model("test")
        self.vector_storage_dir = vector_storage_dir
        os.makedirs(self.vector_storage_dir, exist_ok=True)

    def process_normalized_texts(
        self,
        source_type: Optional[str] = None,
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetches normalized texts from storage, checks caches, computes embeddings, and persists metadata.
        """
        if not self.storage:
            return {"processed": 0, "skipped": 0, "errors": 0}

        records_to_embed = []
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT norm_id, source_type, source_id, normalized_text FROM normalized_texts"
            params: List[Any] = []
            if source_type:
                query += " WHERE source_type = ?"
                params.append(source_type)
            if limit:
                query += f" LIMIT {int(limit)}"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            for r in rows:
                norm_id = r["norm_id"]
                stype = r["source_type"]
                sid = r["source_id"]
                text = r["normalized_text"]
                thash = hashlib.sha256(text.encode("utf-8")).hexdigest()

                # Check if already embedded with current model
                cursor.execute(
                    "SELECT embedding_id, text_hash FROM embedding_records WHERE norm_id = ? AND model_version = ?",
                    (norm_id, self.model.model_name),
                )
                existing = cursor.fetchone()
                if existing and existing["text_hash"] == thash:
                    continue  # Already up to date

                records_to_embed.append({
                    "norm_id": norm_id,
                    "source_type": stype,
                    "source_id": sid,
                    "clean_text": text,
                    "text_hash": thash,
                })

        total = len(rows)
        skipped = total - len(records_to_embed)

        if not records_to_embed or dry_run:
            return {
                "total_eligible": total,
                "embeddings_computed": len(records_to_embed),
                "skipped_cache_hits": skipped,
                "dry_run": dry_run,
            }

        # Compute embeddings in batches
        texts = [r["clean_text"] for r in records_to_embed]
        vectors = self.model.embed(texts)

        # Store vectors in local npy / parquet cache
        safe_model_name = self.model.model_name.replace("/", "_").replace("-", "_")
        vector_file = os.path.join(self.vector_storage_dir, f"vectors_{safe_model_name}.npy")

        # Save or append vectors
        if os.path.exists(vector_file):
            try:
                existing_matrix = np.load(vector_file)
                start_index = len(existing_matrix)
                combined = np.vstack([existing_matrix, vectors])
                np.save(vector_file, combined)
            except Exception:
                start_index = 0
                np.save(vector_file, vectors)
        else:
            start_index = 0
            np.save(vector_file, vectors)

        metadata_records = []
        for i, r in enumerate(records_to_embed):
            emb_id = f"emb_{hashlib.sha256(f'{r['norm_id']}_{self.model.model_name}'.encode()).hexdigest()[:16]}"
            meta = EmbeddingMetadataRecord(
                embedding_id=emb_id,
                norm_id=r["norm_id"],
                source_type=r["source_type"],
                source_id=r["source_id"],
                model_version=self.model.model_name,
                dimension=self.model.dimension,
                text_hash=r["text_hash"],
                is_test_double=self.model.is_test_double,
                vector_file_path=vector_file,
                vector_index=start_index + i,
            )
            metadata_records.append(meta)

        self.storage.upsert_embedding_metadata(metadata_records)

        return {
            "total_eligible": total,
            "embeddings_computed": len(records_to_embed),
            "skipped_cache_hits": skipped,
            "dry_run": False,
        }
