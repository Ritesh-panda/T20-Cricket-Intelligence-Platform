# Evaluation Plan & Benchmarking Protocols: T20 Cricket Intelligence Platform

## 1. Evaluation Philosophy

In accordance with our core engineering standards: **no model choice or analytical claim shall be asserted as superior without empirical evidence**.

All evaluations will run on reproducible, versioned ground-truth datasets with documented evaluation splits, metrics, and seed controls.

---

## 2. Topic Modeling & Clustering Evaluation Framework

### 2.1 Quantitative Intrinsic Metrics

Every clustering experiment (TF-IDF + K-Means, Embeddings + K-Means, HDBSCAN, BERTopic) is scored on:

1. **Silhouette Score ($S$)**: Measures how similar an item is to its own cluster compared to neighboring clusters.
   $$S \in [-1.0, +1.0] \quad (\text{Higher is better})$$
2. **Davies-Bouldin Index ($DBI$)**: Ratio of within-cluster scatter to between-cluster separation.
   $$DBI \ge 0 \quad (\text{Lower is better})$$
3. **Outlier Ratio ($R_{\text{outlier}}$)**: Percentage of documents assigned to noise/unclustered (-1).
   $$R_{\text{outlier}} = \frac{N_{\text{unassigned}}}{N_{\text{total}}}$$
   *(Trade-off: A very low outlier rate may force noise into topics; an excessively high rate renders the model uninformative).*
4. **Topic Coherence ($C_v$ and $NPMI$)**: Measures whether top words in a topic co-occur frequently in sliding windows over the background corpus. Target $C_v > 0.55$.
5. **Cluster Stability**: Measured via Bootstrap Resampling (10 iterations with replacement at 80% subsampling), computing Adjusted Rand Index ($ARI$) across runs.

### 2.2 Human-in-the-Loop Qualitative Interpretability

1. **Word Intrusion Test**: For each topic, 5 top representative keywords are presented along with 1 randomly injected "intruder" word from another topic. Human annotators identify the intruder. High accuracy (>80%) confirms topic coherence.
2. **Topic Intrusion Test**: For a given article, 3 true topic labels and 1 intruder topic label are presented. Annotators identify the irrelevant topic.
3. **Representative Document Alignment**: Evaluates whether the top 3 documents closest to the cluster centroid genuinely embody the top-5 keywords extracted by c-TF-IDF.

---

## 3. Cricket NER & Entity Resolution Evaluation

### 3.1 Gold-Standard Annotation Set (`data/evaluation/ner_gold_sample.jsonl`)
- 200 manually annotated cricket paragraphs sampled across Cricbuzz, ESPNcricinfo, and Wisden.
- Tagged entities: `PLAYER`, `TEAM`, `VENUE`, `PHASE`.
- Ground-truth mapping: Each mention mapped to canonical `player_id` or `team_id`.

### 3.2 Metrics
- **Mention Detection**: Strict and relaxed span-level Precision, Recall, and F1 score.
- **Entity Resolution Accuracy**:
  $$\text{Accuracy}_{\text{ER}} = \frac{\text{Correctly Resolved Mentions}}{\text{Total Detected Mentions}}$$
- **Disambiguation Precision**: Specifically evaluated on ambiguous surnames (e.g., "Sharma" in a match featuring both Rohit and Mohit; "Curran" featuring Sam and Tom).

---

## 4. Sentiment Analysis Evaluation

### 4.1 Evaluation Dataset (`data/evaluation/sentiment_gold_sample.jsonl`)
- 300 annotated cricket sentences categorized as `POSITIVE`, `NEUTRAL`, or `NEGATIVE`.
- Aspect annotations: Evaluates whether positive bowler performance (e.g. "Bumrah dismantled the stumps with an unplayable yorker") is correctly assigned as positive for the bowler and negative for the batter/batting team.

### 4.2 Metrics
- **Macro-Averaged F1 Score** across all 3 classes.
- **Directional Accuracy**: Ensuring match losses are not misclassified as celebratory, and heroic individual efforts in a loss are correctly isolated.

---

## 5. Media-to-Match Event Alignment Evaluation

### 5.1 Gold-Standard Linkage Set (`data/evaluation/alignment_gold_sample.jsonl`)
- 100 hand-verified pairs of:
  `[Article Paragraph]` $\longleftrightarrow$ `[Match ID, Innings, Delivery Over Window]`
- Examples include:
  - Match-winning final over descriptions.
  - Powerplay batting collapses.
  - Pivotal dropped catches or DRS reviews.

### 5.2 Metrics
- **Precision@1**: Is the top-ranked match event window correct?
- **Recall@3**: Does the true event window appear in the top 3 candidate alignments?
- **Mean Reciprocal Rank (MRR)**:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Threshold Calibration**: Precision-Recall curve to establish the optimal confidence threshold $\theta_{\text{link}}$ for accepting an automatic link.

---

## 6. Continuous Logging & Benchmark Dashboard

All evaluation results will be recorded in `data/evaluation/benchmark_results.json` and rendered in the test suite and dashboard:

```json
{
  "benchmark_run_id": "eval_20261020_001",
  "timestamp": "2026-10-20T18:00:00Z",
  "models": {
    "ner_gazetteer_v1": { "precision": 0.92, "recall": 0.88, "f1": 0.90 },
    "clustering_bertopic_v1": { "silhouette": 0.38, "c_v": 0.62, "outlier_rate": 0.12 },
    "clustering_kmeans_tfidf": { "silhouette": 0.14, "c_v": 0.41, "outlier_rate": 0.00 },
    "alignment_hybrid_v1": { "precision@1": 0.84, "recall@3": 0.93, "mrr": 0.88 }
  }
}
```
