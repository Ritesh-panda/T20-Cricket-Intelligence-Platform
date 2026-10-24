# Phase 9 APDI Methodology, Numerical Integrity, and Sensitivity Review

**Document Version**: 1.0.0  
**Date**: 2026-10-24  
**Status**: Formal Audit & Mathematical Sensitivity Analysis  
**Associated Script**: [`scripts/phase9_apdi_sensitivity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/scripts/phase9_apdi_sensitivity.py)  

---

## 1. Conceptual Framework & Definition

The **Attention-to-Performance Discrepancy Index (APDI)** is an empirical, descriptive metric designed to measure the mathematical divergence between an entity's relative media attention share and their relative on-field performance:

$$\text{APDI} = \text{NormAttention} - \text{NormPerformance} \in [-1.0, +1.0]$$

### 1.1 Critical Scientific Boundary
> **Important Research Notice**:  
> APDI is strictly a **descriptive discrepancy metric**. A non-zero APDI value indicates that an entity's volume/prominence of media coverage was not proportional to their athletic percentile rank within the studied cohort.  
> **APDI does NOT prove editorial bias, subjective favoritism, journalist intent, or causal media distortion.** Media attention is driven by narrative prominence, historical rivalry, star power, and human-interest framing, none of which are captured by on-field scorecards.

---

## 2. In-Depth Audit of the 10 Methodological Dimensions

### 2.1 Cohort Definitions & Attention Asymmetry
- **Current Logic**: Entities are segmented into three performance cohorts: `batter`, `bowler`, and `team`. Attention percentiles are computed within each cohort among eligible entities.
- **Audit Finding**: Performance metrics are inherently role-specific (batters produce runs/strike rates; bowlers produce wickets/economy). However, **media attention is holistic**: journalists write about a player as a whole person, not strictly as a batter or bowler. For all-rounders (e.g., Shakib Al Hasan, Hardik Pandya), evaluating them solely in the batting cohort can misrepresent their total athletic contribution.
- **Safeguard**: The storage engine records all-rounders with separate performance metric rows, while APDI evaluates the primary role cohort with complete sample size indicators.

### 2.2 Separate Normalization by Role
- **Audit Finding**: Separating Batters, Bowlers, and Teams into distinct normalization pools is statistically necessary. Combining runs with wickets would require an arbitrary cross-skill exchange rate (e.g., "how many runs is 1 wicket worth?"). By ranking each cohort internally, relative excellence is preserved.

### 2.3 Sample Size Disparities & Discretization
- **Audit Finding**: In the current 10-match bounded corpus, the number of eligible entities meeting the minimum evidence gate is:
  - Eligible Batters: $N = 4$
  - Eligible Bowlers: $N = 2$
  - Eligible Teams: $N = 7$
  - Total Valid: $N = 13$
- **Mathematical Limitation**: With only 2 eligible bowlers (`Kuldeep Yadav` and `Mustafizur Rahman`), the percentile ranks can only take values of $0.00$ and $1.00$. This causes their resulting APDI to jump by large discrete steps ($\pm 0.667$).
- **Conclusion**: In cohorts with $N < 10$, APDI values reflect high discretization granularity. They must be interpreted as broad rank orderings rather than continuous indices.

### 2.4 Performance Composite Formulas
- **Batting Composite**:
  $$\text{Composite}_{\text{bat}} = 0.35 \cdot \text{NormRuns} + 0.35 \cdot \text{NormSR} + 0.30 \cdot \text{NormBoundaryPct}$$
- **Bowling Composite**:
  $$\text{Composite}_{\text{bowl}} = 0.40 \cdot \text{NormWickets} + 0.35 \cdot (1 - \text{NormEconomy}) + 0.25 \cdot \text{NormDotPct}$$
- **Team Composite**:
  $$\text{Composite}_{\text{team}} = 100 \cdot \text{WinPercentage}$$
- **Audit Finding**: The directions are defensible (higher runs/SR/boundaries increase score; lower economy rate increases score via $(1 - \text{NormEconomy})$). However, without Bayesian shrinkage (e.g., regressing strike rates toward cohort mean), a batter with 12 balls faced at a high strike rate can attain an inflated performance score.

### 2.5 Attention Composite Weighting
- **Weighting Structure**:
  - Direct Named Mentions: $1.0\times$
  - Headline Mentions: $3.0\times$ weight
  - Lead Paragraph Mentions: $2.0\times$ weight
- **Audit Finding**: This weighting appropriately reflects media hierarchy (headlines and lead paragraphs signal primary editorial focus). The calculation is deterministic and 100% reproducible.

### 2.6 Mention Inflation & Document Length Bias
- **Audit Finding**: Encyclopedic articles (such as Wikipedia's 104-paragraph tournament overview) generate substantially more mentions for teams like India (52 mentions) than for teams mentioned only in summary tables. Paragraph segmentation mitigates this by tracking unique paragraph reach (`paragraph_count`), but tournament-wide overviews inherently inflate cumulative counts for finalist nations.

### 2.7 Distinguishing Insufficient Data from Zero Attention
- **Current Safeguard**:
  - If an entity faced $< 10$ balls (batter) or bowled $< 12$ legal balls (bowler) or has $0$ editorial mentions:
    $$\text{apdi\_value} = \text{NULL}$$
    $$\text{discrepancy\_category} = \text{INSUFFICIENT\_DATA}$$
- **Audit Finding**: This is a critical scientific safeguard. In naïve implementations, entities with 0 mentions are often given $\text{Attention} = 0$, producing a false "Under-Attended" score of $-0.80$. The platform's explicit preservation of `NULL` avoids this error for 103 out of 116 entities.

### 2.8 Corpus Dependency and Historical Stability
- **Audit Finding**: Because APDI relies on percentile ranks within the active corpus, **ingesting 5 new articles will alter historical percentile ranks**. APDI is therefore not a static player attribute; it is an index of attention within a specified, versioned research window. Every record stores `run_id`, `tournament`, `comparison_window`, and `formula_version`.

### 2.9 Empirical Justification of $\pm 0.20$ Thresholds
- **Audit Finding**: The boundaries $+0.20$ (`OVER_ATTENDED`) and $-0.20$ (`UNDER_ATTENDED`) represent a 20% divergence in percentile rank. They are **heuristic conventions** chosen to define an inner 40% band of reasonable alignment (`BALANCED`).
- **Policy**: These thresholds must be explicitly labeled as **PROVISIONAL**.

---

## 3. Numerical Sensitivity Analysis Results

Using [`scripts/phase9_apdi_sensitivity.py`](file:///c:/Users/Ritesh%20Panda/OneDrive/Desktop/atsma_lab/scripts/phase9_apdi_sensitivity.py), the 13 valid entities were audited across three threshold tiers and two normalization techniques:

### 3.1 Threshold Sensitivity Comparison

| Entity Name | Role | APDI | Thresh $\pm 0.15$ | Thresh $\pm 0.20$ (Base) | Thresh $\pm 0.25$ |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Mustafizur Rahman** | Bowler | **+0.667** | OVER_ATTENDED | OVER_ATTENDED | OVER_ATTENDED |
| **Pakistan** | Team | **+0.500** | OVER_ATTENDED | OVER_ATTENDED | OVER_ATTENDED |
| **Bangladesh** | Team | **+0.333** | OVER_ATTENDED | OVER_ATTENDED | OVER_ATTENDED |
| **Haris Rauf** | Batter | **0.000** | BALANCED | BALANCED | BALANCED |
| **Shakib Al Hasan** | Batter | **0.000** | BALANCED | BALANCED | BALANCED |
| **Arshdeep Singh** | Batter | **0.000** | BALANCED | BALANCED | BALANCED |
| **India** | Team | **0.000** | BALANCED | BALANCED | BALANCED |
| **Canada** | Team | **0.000** | BALANCED | BALANCED | BALANCED |
| **England** | Team | **-0.167** | UNDER_ATTENDED *(shift)* | BALANCED | BALANCED |
| **Australia** | Team | **-0.167** | UNDER_ATTENDED *(shift)* | BALANCED | BALANCED |
| **United States of America** | Team | **-0.500** | UNDER_ATTENDED | UNDER_ATTENDED | UNDER_ATTENDED |
| **Kuldeep Yadav** | Bowler | **-0.667** | UNDER_ATTENDED | UNDER_ATTENDED | UNDER_ATTENDED |
| **Mohammad Rizwan** | Batter | **-1.000** | UNDER_ATTENDED | UNDER_ATTENDED | UNDER_ATTENDED |

#### Distribution Breakdown Across Thresholds:
- **At $\pm 0.15$**: 3 Over-Attended, 5 Balanced, 5 Under-Attended (England and Australia reclassified as Under-Attended).
- **At $\pm 0.20$ (Base)**: 3 Over-Attended, 7 Balanced, 3 Under-Attended.
- **At $\pm 0.25$**: 3 Over-Attended, 7 Balanced, 3 Under-Attended (identical to baseline).

### 3.2 Percentile Rank vs. Min-Max Normalization

| Entity Name | Role | Raw Attn | Raw Perf | Percentile APDI | Min-Max APDI | Divergence ($\Delta$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mustafizur Rahman** | Bowler | 4.50 | 0.00 | **+0.667** | +0.500 | +0.167 |
| **Kuldeep Yadav** | Bowler | 4.50 | 116.08 | **-0.667** | -0.500 | -0.167 |
| **Pakistan** | Team | 73.50 | 0.00 | **+0.500** | +0.629 | -0.129 |
| **Bangladesh** | Team | 22.50 | 0.00 | **+0.333** | +0.143 | +0.190 |
| **India** | Team | 112.50 | 175.00 | **0.000** | 0.000 | 0.000 |
| **Canada** | Team | 19.50 | 0.00 | **0.000** | +0.114 | -0.114 |
| **England** | Team | 28.50 | 100.00 | **-0.167** | -0.371 | +0.205 |
| **Australia** | Team | 27.50 | 62.50 | **-0.167** | -0.167 | 0.000 |
| **USA** | Team | 7.50 | 50.00 | **-0.500** | -0.286 | -0.214 |
| **Mohammad Rizwan** | Batter | 4.50 | 33.46 | **-1.000** | -1.000 | 0.000 |

**Finding**: Min-Max scaling is susceptible to extreme outliers in raw attention (e.g., India's 112.5 raw attention vs USA's 7.5), compressing intermediate teams into narrow sub-ranges. **Percentile ranking is more robust against long-tailed editorial attention distributions.**

---

## 4. Policy and Protocol Recommendations

1. **Retain the Formula**: Keep $\text{APDI} = \text{NormAttention} - \text{NormPerformance}$ for cross-phase comparability.
2. **Label Thresholds**: Display $\pm 0.20$ thresholds in UI and API with `provisional: true`.
3. **Never Replace NULL with Zero**: Maintain `NULL` for `INSUFFICIENT_DATA` to prevent statistical misrepresentation.
4. **Surface Sample Size**: Always display `matches_played`, `balls_faced` / `balls_bowled`, and `paragraph_count` adjacent to APDI scores in API responses and frontend tables.
