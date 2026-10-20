# Research Plan & Experimental Strategy: T20 Cricket Intelligence Platform

## 1. Scientific Context & Research Questions

The core objective of this research is to investigate how unstructured cricket media narratives (journalism and ball-by-ball commentary) can be systematically and measurably grounded in structured match event facts.

### Primary Research Questions (RQs)
- **RQ1 (Unsupervised Topic Discovery)**: Can topic modeling architectures discover nuanced, domain-specific cricket themes (e.g., death-overs bowling execution, middle-order collapse, top-order aggression) without requiring pre-labeled training corpora?
- **RQ2 (Representation Efficacy)**: Do dense semantic embeddings (Sentence Transformers) outperform sparse lexical representations (TF-IDF) in grouping articles reporting on the same underlying match events across disparate publisher vocabularies?
- **RQ3 (Corpus Granularity)**: How does document granularity (paragraph-level news vs. single-ball commentary vs. over-level commentary summaries) affect cluster coherence and outlier rates?
- **RQ4 (Cross-Source Grounding)**: Can a hybrid algorithm combining temporal proximity, named entity overlap, and vector similarity link news passages to specific delivery sequences with high precision and recall?
- **RQ5 (Narrative vs. Reality Gap)**: Does media attention and sentiment correlate directly with player performance metrics (e.g., runs scored, wickets taken, economy rate, MVP index), or do narrative biases over-amplify specific player archetypes?

---

## 2. Experimental Model Matrix for Topic Modeling & Clustering

We establish a rigorous 4-model comparative matrix evaluated on the identical test corpus.

| Experiment ID | Feature Representation | Clustering Algorithm | Dimensionality Reduction | Outlier Strategy | Primary Objective |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-A (Baseline 1)** | TF-IDF (1-3 ngrams, cricket stopwords removed) | K-Means ($k \in [5, 25]$) | None / TruncatedSVD | Forced cluster assignment | Classical lexical baseline |
| **EXP-B (Baseline 2)** | Dense Sentence Embeddings (`all-MiniLM-L6-v2`) | K-Means ($k \in [5, 25]$) | PCA (to 50d) | Forced cluster assignment | Dense semantic baseline with fixed $k$ |
| **EXP-C (Experiment 1)**| Dense Sentence Embeddings (`all-MiniLM-L6-v2`) | HDBSCAN (min_cluster_size=5, min_samples=3) | UMAP (metric=cosine, n_neighbors=15, n_components=5) | Explicit noise rejection (Label -1) | Density-based discovery without forcing outliers into topics |
| **EXP-D (Experiment 2)**| Dense Sentence Embeddings + c-TF-IDF | BERTopic | UMAP + HDBSCAN + c-TF-IDF class representations | Hierarchical topic reduction | State-of-the-art interpretable topic modeling |

---

## 3. Two-Stage Corpus Segmentation Strategy

News articles and ball-by-ball commentary have fundamentally distinct structural and linguistic properties:
- **News Articles**: Macro-narratives, 400–1200 words, rich vocabulary, reflective, delayed by hours/days.
- **Commentary**: Micro-narratives, 10–40 words per delivery, high repetition, immediate real-time capture.

### Stage 1: Independent Intra-Corpus Clustering
1. **Corpus 1 (News Corpus)**: Segmented at paragraph level ($N \approx 5,000$ paragraphs). Run Experiments A, B, C, D.
2. **Corpus 2 (Commentary Corpus)**: Evaluated at two distinct granularities:
   - *Granularity 2a*: Individual delivery descriptions.
   - *Granularity 2b*: Over-level aggregated summaries (combining 6 balls into one tactical micro-narrative).
   - Run Experiments A, B, C, D.

### Stage 2: Cross-Corpus Association Strategies
Once intra-corpus models are evaluated, we benchmark three cross-source linking mechanisms:
- **Strategy S1 (Cluster-to-Cluster Matching)**: Compute cosine similarity between cluster centroid vectors of the News model and Commentary model.
- **Strategy S2 (Shared Embedding Space)**: Project news paragraphs and over-summaries into a shared embedding space, testing whether joint clusters form around specific match events.
- **Strategy S3 (Entity-Temporal-Semantic Hybrid Linker)**: Ground individual news paragraphs to delivery sequences using a multi-feature scoring model.

---

## 4. Media-to-Match Event Alignment Heuristic

For any news paragraph $p$ and candidate match event window $w$ (consisting of deliveries $[d_i, \dots, d_{i+k}]$ from match $M$):

$$\text{Score}(p, w) = w_1 \cdot S_{\text{entity}}(p, M) + w_2 \cdot S_{\text{temporal}}(t_p, t_M) + w_3 \cdot S_{\text{semantic}}(v_p, v_w) + w_4 \cdot S_{\text{event}}(p, w)$$

Where:
- $S_{\text{entity}}$: Jaccard similarity between resolved players/teams in $p$ and participants in event $w$.
- $S_{\text{temporal}}$: Exponential decay penalty based on $|t_p - t_M|$ (publication timestamp vs match end time).
- $S_{\text{semantic}}$: Cosine similarity between sentence embedding of paragraph $p$ and aggregated commentary text of window $w$.
- $S_{\text{event}}$: Binary/weighted boost if specific event descriptors (e.g. "hat-trick", "super over", "review", "six") co-occur in both text sources.
- Parameter tuning: Default weights $w_1 = 0.35, w_2 = 0.30, w_3 = 0.20, w_4 = 0.15$.

---

## 5. Player Attention vs. Performance Index Formulation

To investigate narrative amplification vs. objective contribution:

1. **Objective Performance Metric (Impact Score)**:
   For player $i$ in match $m$, compute composite impact $I_{i, m}$ from Cricsheet data:
   $$I_{i, m} = \frac{\text{Runs}_i}{25} + 2.0 \cdot \text{Wickets}_i + \frac{\text{DotBalls}_i}{6} - \frac{\text{ConcededRuns}_i}{20} + \text{MilestoneBonuses}$$

2. **Media Attention Share**:
   $$A_{i, m} = \frac{\text{Count of Paragraph Mentions}(i, m)}{\sum_j \text{Count of Paragraph Mentions}(j, m)}$$

3. **Attention-to-Performance Ratio ($APR$)**:
   $$APR_{i, m} = \frac{A_{i, m}}{\text{Normalized}(I_{i, m}) + \epsilon}$$

   - $APR > 1.5$: High narrative amplification (player received disproportionate media spotlight).
   - $0.7 \le APR \le 1.3$: Balanced alignment between coverage and on-field impact.
   - $APR < 0.7$: Under-reported performance (quiet match-winner).
