# Phase 9 Research Evaluation Protocol: NLP, Topic Discovery, and Event Alignment

**Document Version**: 1.0.0  
**Date**: 2026-10-24  
**Scope**: Verification Standards, Quantitative Evaluation Protocols, and Reproducibility Bounds  

---

## 1. Natural Language Processing (NLP) Evaluation Protocol

### 1.1 Gold Standard Dataset Integrity (`nlp_gold_set.json`)
The NLP evaluation relies on a benchmark set of 20 annotated entity mentions ([`data/evaluation/nlp_gold_set.json`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/data/evaluation/nlp_gold_set.json)).
- **Independence of Labels**: Gold labels were manually authored based on ground-truth cricket scorecards and roster facts. They were **not** generated or pre-populated by the model's own resolver.
- **Annotation Guidelines**:
  1. `RESOLVED`: The text span unambiguously identifies a unique canonical player or team entity given document-level context (e.g., "Virat Kohli", "Kohli" in Indian innings context).
  2. `AMBIGUOUS`: The surface form matches multiple potential canonical entities without sufficient disambiguating context (e.g., single surname "Sharma" with both Rohit Sharma and Mohit Sharma in gazetteer).
  3. `UNRESOLVED`: The entity is recognized as a cricket participant or nickname but does not match any registered entity in the tournament gazetteer.

### 1.2 Metric Definitions & Mathematical Formulas
1. **Resolution Accuracy**: Fraction of total evaluated mentions whose predicted status and resolved identifier match the gold standard:
   $$\text{Accuracy} = \frac{\sum [(\hat{y}_{\text{status}} = y_{\text{status}}) \land (\hat{y}_{\text{id}} = y_{\text{id}})]}{N}$$
2. **Ambiguity Detection Rate**: Fraction of truly ambiguous mentions correctly flagged as `AMBIGUOUS`:
   $$\text{Ambiguity Rate} = \frac{\text{True Ambiguous Predicted}}{\text{Total Ground-Truth Ambiguous Mentions}}$$
3. **Entity Coverage**: Fraction of non-unresolved mentions successfully resolved or flagged for disambiguation:
   $$\text{Coverage} = \frac{\text{Correctly Resolved} + \text{Ambiguous Detected}}{N}$$
4. **False-Association Rate (Error Rate)**: Fraction of mentions resolved to an incorrect entity identifier:
   $$\text{False-Association Rate} = \frac{\text{Wrongly Resolved}}{N}$$

### 1.3 Reproducible Confusion Counts ($N = 20$)

Executing [`scripts/evaluate_nlp_gold_set.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/scripts/evaluate_nlp_gold_set.py) yields the exact empirical counts:

| Metric Category | Raw Count | Proportion (%) | Benchmark Interpretation |
| :--- | :---: | :---: | :--- |
| **Total Gold Mentions ($N$)** | **20** | 100.0% | Complete test suite sample |
| **Correctly Resolved** | **16** | **80.0%** | Marquee players & unambiguous full names |
| **Ambiguity Detected** | **1** | **5.0%** | Single surname "Sharma" correctly isolated |
| **Unresolved (Out of Vocab)** | **3** | **15.0%** | Nicknames or unregistered entities |
| **Wrongly Resolved (False Associations)** | **0** | **0.0%** | **Zero hallucinated or incorrect links** |
| **Overall Coverage** | **17** | **85.0%** | Resolved + Ambiguous identification |

### 1.4 Known Statistical Boundaries & Limitations
- **Sample Size ($N = 20$)**: Suitable as a deterministic regression gate, but insufficient for statistical generalization across informal social media commentary, dialectal slang, or multilingual match feeds.
- **Single-Surname Ambiguity**: Resolving common surnames ("Khan", "Ali", "Sharma", "Singh") relies on document-level team co-occurrence heuristics. If document team context is missing, resolver conservatively degrades to `AMBIGUOUS`.

---

## 2. Topic Modeling & Semantic Clustering Protocol

### 2.1 Embedding Generation Parameters
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dense Vector Dimensions**: 384
- **Normalization**: Strict L2 unit normalization ($\|\vec{v}\|_2 = 1.0000 \pm 10^{-6}$)
- **Corpus Target**: 314 paragraph records from 5 Wikimedia editorial articles
- **Input Hash**: Stored in `data/processed/embeddings/vectors_sentence_transformers_all_MiniLM_L6_v2.npy`

### 2.2 Clustering Hyperparameters & Reproducibility
- **Algorithm**: `KMeans` (`scikit-learn` v1.6+)
- **Cluster Count ($k$)**: $k = 3$ (optimal silhouette balance)
- **Random Seed**: `random_state = 42`
- **Initializations**: `n_init = 10`
- **Max Iterations**: `max_iter = 300`

### 2.3 Semantic Interpretability & Cluster Profiles

| Cluster ID | Size (Docs) | Top Distinguishing Terms | Silhouette Score | Semantic Interpretation |
| :---: | :---: | :--- | :---: | :--- |
| **Cluster 0** | 120 (38.2%) | `india`, `pakistan`, `rivalry`, `cup`, `match` | **0.108** | **Historical Rivalry & Geopolitics**: Chronicle of India–Pakistan bilateral encounters and historical World Cup tournaments. |
| **Cluster 1** | 94 (29.9%) | `toss`, `elected`, `overs`, `target`, `wickets` | **0.082** | **Tactical Match Encounters**: In-game progression, innings milestones, toss decisions, and scorecard breakdowns. |
| **Cluster 2** | 100 (31.8%) | `squad`, `retrieved`, `june`, `captain`, `reserve` | **0.094** | **Administrative & Rosters**: Official squad selections, player registries, replacements, and citation metadata. |

### 2.4 Comparison Across Alternative Cluster Counts
- **$k = 2$**: Merges Cluster 0 (Rivalry) and Cluster 1 (Match Play). Mean Silhouette $= 0.089$. Less granular domain separation.
- **$k = 3$ (Current)**: Mean Silhouette $= 0.095$. Clean separation between history, match action, and squad administration.
- **$k = 5$**: Sub-segments Cluster 1 into death overs and powerplay, but produces small micro-clusters ($N < 15$). Mean Silhouette drops to $0.076$.

### 2.5 Separation of Reference Pages from Contemporary Journalism
- **Research Guideline**: When expanding the corpus to include contemporary match journalism, reference pages (squad registries, historical rivalry chronicles) must be tagged with `content_type='reference'` and evaluated in a separate topic partition from contemporary match reports (`content_type='news'`).

---

## 3. Cross-Source Alignment Protocol

### 3.1 Non-Fabrication Invariant
The platform requires direct, multi-evidence corroboration before creating an `EventAlignmentRecord`:
1. **Match Association**: The editorial document must have verified evidence linking it to the specific match.
2. **Actor Co-occurrence**: The editorial paragraph must name at least one bowler, batter, or team involved in the specific delivery sequence.
3. **Temporal / Milestone Signal**: The text must reference the specific over window (e.g. "19th over", "final over", "powerplay", "hat-trick").

### 3.2 Explicit Status When Stream is Absent
- **Current Corpus Condition**: Ball-by-ball written commentary entries = **0** (excluded to respect commercial copyright and robots.txt).
- **Evaluation Status**: **`NOT_EVALUABLE`**.
- **Scientific Guardrail**: Rather than fabricating synthetic commentary or matching Wikipedia paragraphs against raw ball timestamps based solely on cosine similarity, the cross-source alignment engine produces **0 alignments**. The API and dashboard report `status: "NOT_EVALUABLE - External ball commentary stream withheld under copyright protocol"`.
