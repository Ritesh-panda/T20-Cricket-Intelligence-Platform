# Media Attention Metrics Specification

## 1. Overview & Theoretical Framework

Media attention in the T20 Cricket Intelligence Platform measures the volume, prominence, breadth, and temporal cadence with which cricket entities (players, teams, events) appear in an acquired editorial corpus.

### Critical Distinction: Available Corpus Reach vs External Audience Reach
- **Article Reach**: Number of distinct articles within our acquired editorial corpus mentioning the entity.
- **Audience Reach / Impressions**: NOT measured by this system. External traffic, impressions, readership, or social shares require external audience monitoring platforms (e.g. Comscore, Google Analytics) and must never be conflated with editorial corpus appearance frequency.

---

## 2. Core Metrics Formulation

### A. Mention Volume (Paragraphs vs Raw Mentions)
Editorial text is chunked into canonical paragraphs (`article_paragraphs`).
- **Paragraph Count ($N_{para}$)**: Number of unique editorial paragraphs mentioning the canonical entity.
  $$\text{ParagraphCount}(e) = |\{ p \in P \mid e \in \text{Entities}(p) \}|$$
- **Raw Mention Count ($N_{raw}$)**: Total raw occurrences of entity mentions.
  A single paragraph mentioning Virat Kohli five times contributes $1$ to $N_{para}$ and $5$ to $N_{raw}$.

### B. Article Reach within Available Corpus
Deduplicates multiple paragraphs from the same article to avoid inflating coverage due to article length.
$$\text{ArticleReach}(e) = |\{ a \in A \mid \exists p \in a \text{ such that } e \in \text{Entities}(p) \}|$$

### C. Publisher / Source Diversity
Measures the number of distinct publisher domains covering an entity to detect single-source coverage spikes.
$$\text{SourceDiversity}(e) = |\{ \text{Domain}(a) \mid a \in \text{Articles}(e) \}|$$

### D. Prominence Scoring
Editorial placement strongly influences reader salience. Position weighting:
- **Headline Mentions ($N_{head}$)**: Mentioned directly in article headline ($\text{weight} = 3.0$).
- **Lead Paragraph Mentions ($N_{lead}$)**: Mentioned in opening paragraph / lead ($\text{weight} = 1.5$).
- **Body Paragraph Mentions ($N_{body}$)**: Mentioned in subsequent paragraphs ($\text{weight} = 1.0$).

$$\text{ProminenceScore}(e) = 3.0 \cdot N_{head} + 1.5 \cdot N_{lead} + 1.0 \cdot N_{body}$$

### E. Event-Linked Attention
Passages explicitly aligned with verified match ball-by-ball events (via cross-source matching or manual curation):
$$\text{EventLinkedMentions}(e) = |\{ p \in \text{Paragraphs}(e) \mid \exists \text{Alignment}(p, \text{event}) \text{ with status } \texttt{ACCEPTED} \}|$$

### F. Temporal Distribution
Bucket attention by match calendar phases:
- `pre_match`: Articles published prior to match date.
- `during_match`: Commentary and live updates on match day.
- `post_match`: Post-match reviews and tactical analyses.
- `date_only`: Preserved when publication timestamps lack sub-day precision.

### G. Raw Attention Composite
For cohort percentile normalization:
$$\text{RawAttentionComposite}(e) = 1.0 \cdot N_{para} + 2.0 \cdot \text{ArticleReach} + 1.5 \cdot \text{SourceDiversity} + \text{ProminenceBonus}$$
where $\text{ProminenceBonus} = 2.0 \cdot N_{head} + 1.0 \cdot N_{lead}$.
