# Attention-to-Performance Discrepancy Index (APDI) Methodology

## 1. Objective & Research Question

The core research question of the platform is:
> *Which players, teams, and match events receive disproportionately high or low media attention relative to their objectively measured performance, and what evidence supports that discrepancy?*

Media attention and cricket performance use incompatible units (paragraphs vs runs/wickets). Subtracting raw counts directly is statistically indefensible. APDI resolves this through **Role-Cohort Percentile Normalization**.

---

## 2. Cohort Definition & Quality Eligibility Gates

Entities are segmented into role cohorts to prevent comparing batters against bowlers:
1. **Batter Cohort**: Players who primary role or match participation involves batting ($\ge 10$ balls faced).
2. **Bowler Cohort**: Players who bowled $\ge 12$ legal balls.
3. **All-Rounder Cohort**: Players meeting both thresholds.
4. **Team Cohort**: All competing teams in the tournament.

### Data Sufficiency Thresholds
An entity receives `INSUFFICIENT_DATA` (with no APDI score calculated) if:
- Matches played $< 1$.
- Editorial paragraphs in corpus $< 1$.
- Minimum balls faced/bowled not reached.
- Cohort size $< 2$ (cannot establish relative ranking).

---

## 3. Normalization Formula: Percentile Ranks

Within each eligible cohort of size $N \ge 2$:
1. Entities are sorted in ascending order of raw composite score:
   $$\text{Rank}(e) \in \{0, 1, \dots, N - 1\}$$
2. The normalized score maps strictly to $[0.0, 1.0]$:
   $$\text{NormalizedScore}(e) = \frac{\text{Rank}(e)}{N - 1}$$

- $\text{NormAttention}(e) \in [0.0, 1.0]$
- $\text{NormPerformance}(e) \in [0.0, 1.0]$

---

## 4. Discrepancy Index Formulation

$$\text{APDI}(e) = \text{NormAttention}(e) - \text{NormPerformance}(e) \in [-1.0, +1.0]$$

### Classification Thresholds:
- **$\text{APDI} > +0.20$**: `OVER_ATTENDED`
  - Editorial spotlight significantly exceeds objective on-field contribution.
- **$\text{APDI} < -0.20$**: `UNDER_ATTENDED`
  - High on-field performance with disproportionately low media spotlight.
- **$-0.20 \le \text{APDI} \le +0.20$**: `BALANCED`
  - Media attention is broadly proportionate to objective performance.
- **Missing or Insufficient Inputs**: `INSUFFICIENT_DATA`
  - APDI value is `null`. No speculative score is assigned.

---

## 5. Non-Causal & Scientific Disclaimers
1. **No Psychological Bias Imputation**: APDI measures an empirical discrepancy between corpus frequency and match statistics. It does not prove conscious malice, racial bias, or systemic favoritism by journalists.
2. **Corpus Boundary**: The index reflects the *acquired* editorial corpus, not all cricket journalism globally.
