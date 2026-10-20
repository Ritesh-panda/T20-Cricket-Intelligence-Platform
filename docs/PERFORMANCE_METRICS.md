# Cricket Performance Metrics Specification

## 1. Overview & Source of Truth

Objective performance statistics are derived exclusively from verified, canonical ball-by-ball delivery records (`deliveries`) and match records (`matches`). Under no circumstances are statistics extracted or inferred from editorial journalistic prose.

---

## 2. Cricket Scoring Rules & Invariants

To avoid naive statistical aggregation, the analytics engine strictly adheres to standard ICC Laws of Cricket:

### A. Extras Handling
1. **Wides (`extra_type == 'wides'`)**:
   - Count toward bowling runs conceded.
   - Do **NOT** count as legal balls bowled.
   - Do **NOT** count as balls faced by the batter.
2. **No-Balls (`extra_type == 'noballs'`)**:
   - Count toward bowling runs conceded.
   - Do **NOT** count as legal balls bowled.
   - **DO** count as balls faced by the batter.
3. **Byes & Leg-Byes (`extra_type in ('byes', 'legbyes', 'penalty')`)**:
   - Are fielding / team extras.
   - Are **NOT** charged against the bowler's individual figures.
   - Batter runs off these balls are zero.

### B. Bowler-Credited Dismissals
Only official bowler dismissals are credited to the bowler:
- **Credited**: `bowled`, `caught`, `caught and bowled`, `lbw`, `stumped`, `hit wicket`.
- **Not Credited**: `run out`, `retired hurt`, `retired out`, `obstructing the field`.

---

## 3. Mathematical Formulations

### A. Batting Statistics
- **Balls Faced ($BF$)**: Deliveries where `extra_type != 'wides'`.
- **Strike Rate ($SR$)**: $\frac{\text{Runs Scored}}{BF} \times 100 \quad (BF > 0)$.
- **Batting Average ($BA$)**: $\frac{\text{Runs Scored}}{\text{Dismissals}} \quad (\text{Dismissals} > 0)$.
- **Boundary Count**: Distinct deliveries where `batter_runs == 4` (Fours) or `6` (Sixes).

### B. Bowling Statistics
- **Legal Balls ($LB$)**: Deliveries where `is_legal == 1`.
- **Overs Display Format**: $\lfloor LB / 6 \rfloor + (LB \pmod 6) / 10.0$ (e.g. 4.2 overs).
- **Completed Overs ($O$)**: $LB / 6.0$.
- **Bowling Economy ($Econ$)**: $\frac{\text{Runs Conceded} \times 6}{LB} \quad (LB > 0)$.
- **Bowling Average ($BwAvg$)**: $\frac{\text{Runs Conceded}}{\text{Wickets Taken}} \quad (\text{Wickets} > 0)$.
- **Bowling Strike Rate ($BwSR$)**: $\frac{LB}{\text{Wickets Taken}} \quad (\text{Wickets} > 0)$.

### C. Match Phase Contributions
- **Powerplay**: Overs 0 to 5.
- **Middle**: Overs 6 to 14.
- **Death**: Overs 15 to 19.

### D. Role-Specific Raw Composites
- **Batter Composite**:
  $$\text{RawBatting} = \text{Runs} + 0.5 \cdot \max(-50, \min(100, SR - 100)) + 2.0 \cdot \text{Sixes} + 1.0 \cdot \text{Fours}$$
- **Bowler Composite**:
  $$\text{RawBowling} = 20.0 \cdot \text{Wickets} + 2.0 \cdot \max(0, (8.0 - Econ) \cdot O) + 5.0 \cdot \text{DeathWickets}$$
- **Team Composite**:
  $$\text{RawTeam} = 25.0 \cdot \text{Wins} + 0.75 \cdot \text{WinPct}$$
