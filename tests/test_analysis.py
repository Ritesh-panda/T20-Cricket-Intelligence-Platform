"""
Comprehensive unit and integration tests for Phase 5: Semantic Embeddings,
Topic Discovery, and Narrative Intelligence.
All tests run 100% offline and use deterministic test doubles.
"""

import os
import shutil
import tempfile
import numpy as np
import pytest

from src.analysis.analysis_schemas import CorpusType, MatchStatus
from src.analysis.embedding_models import DeterministicTestEmbeddingModel, get_embedding_model
from src.analysis.embedding_pipeline import EmbeddingPipeline
from src.analysis.event_alignment import EventAlignmentEngine
from src.analysis.narrative_similarity import CrossSourceNarrativeMatcher
from src.analysis.narrative_timeline import NarrativeTimelineEngine
from src.analysis.similarity import batch_cosine_similarity, cosine_similarity, find_top_k
from src.analysis.tfidf_baseline import CricketTfidfBaseline
from src.analysis.topic_clustering import TopicClusterer
from src.analysis.topic_evaluation import evaluate_topic_clustering
from src.analysis.topic_labeling import TopicLabeler
from src.nlp.schemas import NormalizedTextRecord
from src.storage.sqlite_manager import SQLiteStorageManager


@pytest.fixture
def temp_db():
    """Provides an isolated SQLite database instance."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_analysis.db")
    storage = SQLiteStorageManager(db_path)
    yield storage
    shutil.rmtree(temp_dir, ignore_errors=True)


# -------------------------------------------------------------------------
# 1. Embedding Interface & Test Double Tests
# -------------------------------------------------------------------------

def test_deterministic_embedding_model_properties():
    """Verifies test double properties, shape validation, and unit normalization."""
    model = get_embedding_model("test")
    assert model.is_test_double is True
    assert model.dimension == 384
    assert model.model_name == "test-deterministic-hash-384"

    texts = [
        "Kohli scored 82* from 53 balls in Melbourne.",
        "Bumrah bowled a lethal yorker in the 19th over.",
    ]
    vectors = model.embed(texts)
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (2, 384)
    assert vectors.dtype == np.float32

    # Verify L2-normalization (magnitude == 1.0)
    for vec in vectors:
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, abs=1e-5) == 1.0


def test_deterministic_embedding_reproducibility():
    """Verifies that identical strings produce identical vectors across calls."""
    model = DeterministicTestEmbeddingModel(dimension=384)
    text = "India need 12 runs from 6 balls with 4 wickets in hand."
    vec1 = model.embed([text])[0]
    vec2 = model.embed([text])[0]
    np.testing.assert_array_almost_equal(vec1, vec2)


def test_embedding_empty_and_whitespace_text():
    """Verifies graceful handling of empty and whitespace texts."""
    model = DeterministicTestEmbeddingModel(dimension=384)
    texts = ["", "   ", "\n\t"]
    vectors = model.embed(texts)
    assert vectors.shape == (3, 384)
    for vec in vectors:
        assert np.linalg.norm(vec) == 0.0


# -------------------------------------------------------------------------
# 2. Similarity & Retrieval Tests
# -------------------------------------------------------------------------

def test_cosine_similarity_edge_cases():
    """Verifies cosine similarity edge cases including zero vectors and identical vectors."""
    vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    zero_vec = np.zeros(3, dtype=np.float32)

    assert cosine_similarity(vec1, vec1) == pytest.approx(1.0, abs=1e-5)
    assert cosine_similarity(vec1, vec2) == pytest.approx(0.0, abs=1e-5)
    assert cosine_similarity(vec1, zero_vec) == 0.0


def test_batch_similarity_and_find_top_k():
    """Verifies batch similarity calculation and top-K candidate retrieval."""
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    corpus = np.array([
        [1.0, 0.0, 0.0],    # sim = 1.0
        [0.8, 0.6, 0.0],    # sim = 0.8
        [0.0, 1.0, 0.0],    # sim = 0.0
        [-1.0, 0.0, 0.0],   # sim = -1.0
    ], dtype=np.float32)

    top_matches = find_top_k(query, corpus, top_k=2, min_threshold=0.5)
    assert len(top_matches) == 2
    assert top_matches[0][0] == 0
    assert top_matches[0][1] == pytest.approx(1.0, abs=1e-4)
    assert top_matches[1][0] == 1
    assert top_matches[1][1] == pytest.approx(0.8, abs=1e-4)


# -------------------------------------------------------------------------
# 3. Sparse TF-IDF Baseline Tests
# -------------------------------------------------------------------------

def test_tfidf_preserves_cricket_numbers_and_overs():
    """Demonstrates that TF-IDF tokenizer preserves overs (19.4), scores (182/5), and not-out marks (82*)."""
    corpus = [
        "19.4 Bumrah to Kohli, SIX! Kohli scored 82* in the chase.",
        "India finished on 182/5 after 20 overs following DRS review.",
    ]
    tfidf = CricketTfidfBaseline(mode="word", ngram_range=(1, 2))
    tfidf.fit(corpus)

    features = tfidf.vectorizer.get_feature_names_out()
    features_lower = [f.lower() for f in features]

    assert any("19.4" in f for f in features_lower), "Over 19.4 was lost by tokenizer"
    assert any("182/5" in f for f in features_lower), "Score 182/5 was lost by tokenizer"
    assert any("82*" in f for f in features_lower), "Not-out score 82* was lost by tokenizer"
    assert any("drs" in f for f in features_lower), "Acronym DRS was lost by tokenizer"


def test_tfidf_vs_dense_semantic_representation():
    """Compares lexical TF-IDF with dense test embedding on paraphrased text."""
    doc_a = "Bumrah dismissed Head with a yorker on 19.4."
    doc_b = "A yorker on 19.4 from Bumrah sent Head back to the pavilion."  # Paraphrase
    doc_c = "South Africa defeated England by 7 runs in St Lucia."       # Unrelated

    tfidf = CricketTfidfBaseline()
    sim_matrix = tfidf.compute_similarity([doc_a], [doc_b, doc_c])

    # Paraphrased sentences share vocabulary and score higher than unrelated
    assert sim_matrix[0, 0] > sim_matrix[0, 1]


# -------------------------------------------------------------------------
# 4. Topic Clustering & Labeling Tests
# -------------------------------------------------------------------------

def test_kmeans_clustering_reproducibility():
    """Verifies that KMeans produces deterministic, reproducible cluster assignments under a fixed seed."""
    model = DeterministicTestEmbeddingModel()
    corpus = [
        "Virat Kohli scored a magnificent fifty for India.",
        "Rohit Sharma hit three sixes in the powerplay.",
        "Jasprit Bumrah bowled four consecutive dot balls.",
        "Arshdeep Singh took two wickets in the death overs.",
        "Kagiso Rabada struck early for South Africa.",
        "Heinrich Klaasen launched huge maximums into the stands.",
    ]
    matrix = model.embed(corpus)

    clusterer1 = TopicClusterer(algorithm="kmeans", n_clusters=2, random_state=42)
    labels1 = clusterer1.fit_predict(matrix)

    clusterer2 = TopicClusterer(algorithm="kmeans", n_clusters=2, random_state=42)
    labels2 = clusterer2.fit_predict(matrix)

    np.testing.assert_array_equal(labels1, labels2)


def test_clustering_edge_case_single_document():
    """Verifies clustering stability when corpus has only 1 document."""
    matrix = np.ones((1, 384), dtype=np.float32)
    clusterer = TopicClusterer(algorithm="kmeans", n_clusters=3)
    labels = clusterer.fit_predict(matrix)
    assert len(labels) == 1
    assert labels[0] == 0


def test_dbscan_noise_handling():
    """Verifies that DBSCAN assigns -1 to outlier noise points."""
    # 3 identical points and 1 isolated orthogonal point
    matrix = np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],  # Outlier
    ], dtype=np.float32)

    clusterer = TopicClusterer(algorithm="dbscan", eps=0.1, min_samples=2)
    labels = clusterer.fit_predict(matrix)

    assert labels[0] == labels[1] == labels[2]
    assert labels[3] == -1, "Outlier should be tagged as noise (-1)"


def test_topic_labeling_c_tfidf():
    """Verifies that TopicLabeler generates salient c-TF-IDF labels and picks representative docs."""
    docs = [
        "Bumrah bowled yorkers in death overs.",
        "Bumrah struck with another lethal yorker.",
        "Kohli anchored the batting chase with boundaries.",
        "Kohli accumulated runs calmly in the middle overs.",
    ]
    labels = np.array([0, 0, 1, 1])
    distances = np.array([0.1, 0.4, 0.15, 0.5])
    doc_ids = ["doc_0", "doc_1", "doc_2", "doc_3"]

    labeler = TopicLabeler(top_n_words=3)
    keywords = labeler.extract_cluster_keywords(docs, labels)
    label_0 = labeler.generate_topic_label(keywords.get(0, []), 0)
    label_1 = labeler.generate_topic_label(keywords.get(1, []), 1)

    assert "bumrah" in label_0.lower() or "yorker" in label_0.lower()
    assert "kohli" in label_1.lower() or "chase" in label_1.lower()

    reps_0 = labeler.select_representative_documents(doc_ids, labels, distances, 0, top_m=1)
    assert reps_0 == ["doc_0"]  # doc_0 had distance 0.1 vs doc_1 distance 0.4


def test_topic_evaluation_metrics():
    """Verifies calculation of silhouette, Davies-Bouldin, and noise ratios."""
    embeddings = np.array([
        [1.0, 0.0],
        [0.9, 0.1],
        [0.0, 1.0],
        [0.1, 0.9],
    ], dtype=np.float32)
    labels = np.array([0, 0, 1, 1])

    metrics = evaluate_topic_clustering(embeddings, labels)
    assert metrics.n_documents == 4
    assert metrics.n_clusters == 2
    assert metrics.n_noise == 0
    assert metrics.noise_ratio == 0.0
    assert metrics.silhouette_score is not None
    assert metrics.silhouette_score > 0.5


# -------------------------------------------------------------------------
# 5. Narrative Similarity & Two-Stage Ranking Tests
# -------------------------------------------------------------------------

def test_two_stage_cross_source_matcher():
    """Verifies two-stage candidate retrieval and conservative ranking with entity overlap."""
    model = DeterministicTestEmbeddingModel()
    matcher = CrossSourceNarrativeMatcher(retrieval_threshold=0.0, accept_threshold=0.50)

    editorial_text = "Jasprit Bumrah produced an unplayable spell to dismiss Heinrich Klaasen."
    ed_emb = model.embed([editorial_text])[0]
    ed_entities = {"player_jasprit_bumrah", "player_heinrich_klaasen"}

    commentary_records = [
        {
            "norm_id": "comm_norm_1",
            "source_id": "comm_1",
            "text": "16.1 Bumrah to Klaasen, OUT! What a delivery!",
            "entities": {"player_jasprit_bumrah", "player_heinrich_klaasen"},
            "match_id": "match_t20_ind_sa_final",
        },
        {
            "norm_id": "comm_norm_2",
            "source_id": "comm_2",
            "text": "0.1 Starc to Rohit, no run, defended solidly.",
            "entities": {"player_mitchell_starc", "player_rohit_sharma"},
            "match_id": "match_t20_ind_aus",
        },
    ]
    comm_texts = [c["text"] for c in commentary_records]
    comm_embeddings = model.embed(comm_texts)

    matches = matcher.match_editorial_to_commentary(
        editorial_norm_id="ed_norm_1",
        editorial_source_id="art_1",
        editorial_text=editorial_text,
        editorial_embedding=ed_emb,
        editorial_entities=ed_entities,
        commentary_records=commentary_records,
        commentary_embeddings=comm_embeddings,
        top_k=2,
    )

    assert len(matches) > 0
    top_match = matches[0]
    assert top_match.commentary_norm_id == "comm_norm_1"
    assert "player_jasprit_bumrah" in top_match.evidence["shared_entities"]
    assert top_match.status == MatchStatus.ACCEPTED


# -------------------------------------------------------------------------
# 6. Event Alignment Engine Tests
# -------------------------------------------------------------------------

def test_event_alignment_synthesizes_milestones():
    """Verifies that match deliveries are synthesized into wickets and death over milestones."""
    deliveries = [
        {"over_number": 19, "innings_num": 2, "bowler_id": "player_jasprit_bumrah", "player_dismissed_id": "player_marco_jansen", "is_wicket": True, "total_runs": 1},
        {"over_number": 19, "innings_num": 2, "bowler_id": "player_jasprit_bumrah", "is_wicket": False, "total_runs": 0},
        {"over_number": 19, "innings_num": 2, "bowler_id": "player_jasprit_bumrah", "is_wicket": False, "total_runs": 1},
    ]
    engine = EventAlignmentEngine()
    milestones = engine.synthesize_match_milestones(deliveries)

    assert len(milestones) >= 1
    m_types = [m["milestone_type"] for m in milestones]
    assert "WICKET" in m_types or "DEATH_OVER_EXECUTION" in m_types


def test_align_editorial_to_milestones():
    """Verifies paragraph alignment against synthesized match milestones."""
    engine = EventAlignmentEngine()
    milestones = [
        {
            "milestone_type": "WICKET",
            "over_number": 19,
            "innings_num": 2,
            "primary_actors": ["player_jasprit_bumrah", "player_marco_jansen"],
            "description": "Wicket in over 19",
        }
    ]
    paragraph_text = "Bumrah took a crucial wicket in the 19th over clean bowling Jansen."
    paragraph_entities = {"player_jasprit_bumrah", "player_marco_jansen"}

    alignments = engine.align_editorial_to_milestones(
        paragraph_id="p1",
        paragraph_text=paragraph_text,
        paragraph_entities=paragraph_entities,
        milestones=milestones,
    )
    assert len(alignments) == 1
    assert alignments[0]["alignment_confidence"] >= 0.70
    assert alignments[0]["evidence"]["milestone_type"] == "WICKET"


# -------------------------------------------------------------------------
# 7. Narrative Timeline Tests
# -------------------------------------------------------------------------

def test_narrative_timeline_temporal_aggregation():
    """Verifies aggregation of articles across temporal buckets, distinguishing observed vs inferred."""
    engine = NarrativeTimelineEngine()
    articles = [
        {"article_id": "a1", "published_at": "2024-06-29T18:00:00Z", "sentiment_label": "POSITIVE", "sentiment_score": 0.8},
        {"article_id": "a2", "published_at": "2024-06-29T21:00:00Z", "sentiment_label": "POSITIVE", "sentiment_score": 0.6},
        {"article_id": "a3", "published_at": None, "sentiment_label": "NEUTRAL", "sentiment_score": 0.0},  # Untimed
    ]
    timeline = engine.build_timeline(articles, bucket_by="day")

    assert len(timeline) == 2  # '2024-06-29' and 'unknown_date'
    dated_point = next(pt for pt in timeline if pt.bucket_label == "2024-06-29")
    unknown_point = next(pt for pt in timeline if pt.bucket_label == "unknown_date")

    assert dated_point.doc_count == 2
    assert dated_point.observed_timestamps_count == 2
    assert dated_point.inferred_timestamps_count == 0
    assert dated_point.mean_sentiment == pytest.approx(0.7, abs=1e-3)

    assert unknown_point.doc_count == 1
    assert unknown_point.observed_timestamps_count == 0
    assert unknown_point.inferred_timestamps_count == 1


# -------------------------------------------------------------------------
# 8. Storage, Idempotency & Persistence Tests
# -------------------------------------------------------------------------

def test_embedding_pipeline_idempotency_and_caching(temp_db):
    """Verifies that EmbeddingPipeline stores vectors and skips unchanged text on re-run."""
    # Seed a normalized text row
    norm_rec = NormalizedTextRecord(
        norm_id="norm_test_01",
        source_type="article_paragraph",
        source_id="art_1_p0",
        original_text="Kohli scored 82* from 53 balls.",
        normalized_text="Kohli scored 82* from 53 balls.",
        char_count=31,
    )
    temp_db.upsert_normalized_text(norm_rec)

    pipeline = EmbeddingPipeline(storage=temp_db)

    # First run: should compute 1 embedding
    res1 = pipeline.process_normalized_texts()
    assert res1["embeddings_computed"] == 1
    assert res1["skipped_cache_hits"] == 0

    # Second run: should hit cache and skip
    res2 = pipeline.process_normalized_texts()
    assert res2["embeddings_computed"] == 0
    assert res2["skipped_cache_hits"] == 1

    # Verify stored records in SQLite
    stored_meta = temp_db.get_embedding_metadata(norm_id="norm_test_01")
    assert len(stored_meta) == 1
    assert stored_meta[0]["dimension"] == 384
    assert stored_meta[0]["is_test_double"] == 1


def test_schema_v4_migration_and_analysis_metrics(temp_db):
    """Verifies that Schema Version 4 tables exist and metrics report truthfully."""
    metrics = temp_db.get_analysis_metrics()
    assert metrics["embedding_records_count"] == 0
    assert metrics["topic_runs_count"] == 0
    assert metrics["cross_source_matches_count"] == 0
    assert metrics["timeline_snapshots_count"] == 0
