# C9 — Ranking-Based Candidate Selection and Robustness

## 1. Contract identity

- **Project:** `psx-ml-research`
- **Contract:** `C9_RANKING_BASED_CANDIDATE_SELECTION_AND_ROBUSTNESS`
- **Required branch:** `feature/c9-ranking-selection-robustness`
- **Base:** accepted C8 merged into `main`
- **Canonical universe:** `pit_liquid_ordinary_equity_v1`
- **Primary horizon:** 5 sessions
- **Secondary diagnostic horizon:** 10 sessions
- **Canonical target:** 5-session market-relative cross-sectional rank
- **Canonical models:** LightGBM CPU and XGBoost CUDA verification
- **Canonical feature set:** `B_market_context`
- **Reference feature set:** `A_c7_only`
- **Final 2026 holdout:** remains locked

C9 must be implemented, reviewed and accepted on its own branch. It must not be merged into `main` until all acceptance tests pass and the contract is explicitly accepted.

## 2. Purpose

C8 established qualified positive evidence that the 5-session market-relative rank target is predictable:

```text
LightGBM B_market_context:
mean daily IC ≈ 0.1087
fold ICs ≈ 0.0993, 0.1030, 0.1239

XGBoost B_market_context:
mean daily IC ≈ 0.1022
fold ICs ≈ 0.0898, 0.0948, 0.1219
```

C9 asks:

> Can that ranking be turned into a stable, repeatable candidate-selection process that survives threshold, turnover, liquidity, concentration, regime and model-agreement checks?

C9 remains a predictive research contract. It must not claim implementable profitability.

## 3. Scope

### In scope

- top-k and percentile candidate selection;
- bottom-tail avoidance analysis;
- rebalance-schedule comparisons;
- liquidity screens;
- sector caps and sector-neutral selection;
- turnover, persistence and candidate churn;
- model agreement and simple rank ensembles;
- threshold, fold, regime, date, symbol and sector robustness;
- random, momentum, liquidity and C8-regression baselines;
- fixed policy recommendation for C10;
- Signal Viewer-compatible summary artifacts.

### Out of scope

- fees, taxes, spread, slippage or market impact;
- portfolio accounting or capital allocation;
- realized P&L, Sharpe ratio or drawdown;
- stops, take-profit, position sizing or leverage;
- live execution or trading signals;
- hyperparameter searches;
- news, deep learning or 2026 holdout access.

## 4. Source boundaries

Expected inputs:

```text
artifacts/predictions/c8/
artifacts/models/c8/
artifacts/reports/C8_MODEL_REPORT.md
artifacts/reports/C8_MANIFEST.json
data/processed/model_inputs/c8/
data/processed/features/
data/processed/targets/c8_relative_targets.parquet
data/processed/universe/c6_universe_membership.parquet
data/processed/datasets/temporal_split_assignments.parquet
config/
```

C9 must not:

- connect to SQLite;
- read or modify `psx_watcher.db`;
- modify `psx-stock-watcher`;
- modify Signal Viewer code;
- fetch live data;
- overwrite C1–C8 artifacts;
- access 2026 rows;
- retrain using validation or holdout information;
- alter C8 target or feature definitions silently.

## 5. Canonical model inputs

### Primary task

```text
target:
fwd_market_relative_rank_5s

features:
B_market_context

models:
LightGBM CPU
XGBoost CUDA
```

### Required references

```text
5-session rank + A_c7_only
10-session rank + B_market_context
```

Optional diagnostic:

```text
5-session rank + D_full_context
```

C9 is not a broad model-search contract.

## 6. Prediction provenance

Reuse accepted C8 out-of-fold predictions wherever possible.

If rerunning is necessary, preserve:

- C8 folds;
- target;
- feature order;
- model configuration;
- seeds;
- early stopping;
- prediction reconciliation.

Every prediction row must include:

```text
trade_date
symbol
fold
horizon
target_family
feature_variant
model
prediction
actual_rank_target
actual_market_relative_return
sector
liquidity attributes
market-regime attributes
prediction provenance
```

## 7. Candidate-selection policies

### Percentile policies

```text
top_5pct
top_10pct
top_20pct
bottom_5pct
bottom_10pct
bottom_20pct
```

### Fixed-count policies

```text
top_5
top_10
top_20
bottom_5
bottom_10
bottom_20
```

### Rank thresholds

```text
prediction rank >= 0.80
prediction rank >= 0.90
prediction rank >= 0.95
prediction rank <= 0.20
prediction rank <= 0.10
prediction rank <= 0.05
```

Evaluate separately:

```text
top-tail selection
bottom-tail avoidance
top-minus-bottom diagnostic spread
```

Bottom-tail work is diagnostic only, not a short-selling strategy.

## 8. Rebalance schedules

Required:

```text
daily
every_2_sessions
weekly_first_session
weekly_last_session
non_overlapping_5_session
```

Optional predefined diagnostics:

```text
Monday_only
Friday_only
```

Friday-only is exploratory and must not be interpreted causally.

## 9. Holding-window alignment

Canonical outcome:

```text
select on date t
evaluate market-relative return over t+1 through t+5
```

Maintain separate views for:

```text
overlapping daily selections
non-overlapping 5-session selections
weekly selections
```

No portfolio-return aggregation is allowed.

## 10. Candidate outcome metrics

For every policy/date/model/fold/subset:

```text
candidate count
mean actual market-relative return
median actual market-relative return
mean actual rank
median actual rank
top-decile hit rate
top-quintile hit rate
bottom-decile contamination rate
positive-relative-return fraction
spread versus unselected universe
spread versus universe median
```

Aggregate:

```text
date-level mean and median
date-block bootstrap 95% CI
positive-date fraction
worst and best fold
fold standard deviation
```

## 11. Ranking metrics

Required:

```text
precision@5, @10, @20
recall@5, @10, @20
NDCG@5, @10, @20
top-decile capture
bottom-decile rejection
mean reciprocal rank of actual top-decile stocks
```

Definitions must be explicit and date-local.

## 12. Turnover and persistence

Required:

```text
1-day, 2-day and 5-day retention
Jaccard overlap between consecutive selections
entries and exits
gross candidate turnover
rank-change distribution
candidate lifetime
```

Report mean, median, 95th percentile, fold and regime results.

Turnover remains diagnostic; costs belong to C10.

## 13. Rank persistence

Required:

```text
prediction-rank autocorrelation at lags 1, 2 and 5
top-decile persistence
bottom-decile persistence
selected-stock retention
selected stock falling below median
unselected stock entering top tail
```

## 14. Liquidity screens

### L0

```text
pit_liquid_ordinary_equity_v1
```

### L1

```text
top 75% by rolling 20-session turnover within each date
```

### L2

```text
top 50% by rolling 20-session turnover within each date
```

### L3

Optional fixed absolute-turnover threshold only if reliable point-in-time units exist.

Report counts, outcomes, turnover, concentration and model agreement.

## 15. Sector constraints

### S0 — Unconstrained

### S1 — Maximum two candidates per sector

```text
max_per_sector = 2
```

### S2 — Maximum one candidate per sector

```text
max_per_sector = 1
```

### S3 — Sector-neutral

Select the highest-ranked eligible stock in each sufficiently populated sector.

Report skipped sectors explicitly.

## 16. Concentration diagnostics

Required:

```text
sector Herfindahl index
symbol Herfindahl index
top-sector selection share
top-5-sector share
top-symbol selection frequency
top-10-symbol selection frequency
date concentration
```

Determine whether performance is driven by a few symbols, sectors, dates, folds or regimes.

## 17. Model agreement

Compare LightGBM and XGBoost by date:

```text
rank correlation
top-5 overlap
top-10 overlap
top-20 overlap
top-decile overlap
bottom-decile overlap
```

Aggregate by fold and regime.

## 18. Ensemble ranking

Required fixed variants:

### E0

LightGBM only.

### E1

XGBoost only.

### E2

```text
ensemble_rank =
0.5 * lightgbm_percentile_rank
+ 0.5 * xgboost_percentile_rank
```

### E3

Consensus-only selection: symbols selected by both models.

No learned ensemble weights are allowed.

## 19. Ensemble decision rules

Required:

```text
top 10% by LightGBM
top 10% by XGBoost
top 10% by average-rank ensemble
intersection of both top-10% sets
union of both top-10% sets
```

Report coverage, count, outcome, precision, turnover and concentration.

## 20. Market-regime robustness

Use C8 point-in-time regimes:

```text
trend: positive / neutral / negative
volatility: low / medium / high
breadth: narrow / neutral / broad
dispersion: low / medium / high
```

For every canonical policy, report outcome, positive-date fraction, precision, turnover and model agreement.

## 21. Fold robustness

Required:

```text
fold_2023
fold_2024
fold_2025
```

A rule is not robust if it depends on one fold or requires fold-specific thresholds.

## 22. Date concentration

Required:

```text
share of aggregate advantage from top 5, 10 and 20 dates
leave-top-5-dates-out
leave-top-10-dates-out
```

## 23. Symbol concentration

Required:

```text
selection frequency by symbol
outcome and contribution by symbol
leave-top-5-symbols-out
leave-top-10-symbols-out
```

## 24. Sector concentration

Required:

```text
selection frequency by sector
outcome and contribution by sector
leave-top-sector-out
leave-top-3-sectors-out
```

## 25. Threshold robustness

Compare:

```text
top 5%
top 10%
top 20%
top 5
top 10
top 20
```

A result is fragile if only one exact threshold works.

## 26. Rebalance robustness

Compare:

```text
daily
every 2 sessions
weekly first session
weekly last session
non-overlapping 5-session
```

Prefer slower schedules when signal quality is preserved.

## 27. Bottom-tail avoidance

Required:

```text
actual relative outcome of predicted bottom 5%, 10% and 20%
universe outcome after excluding predicted bottom tail
```

No short-strategy claim.

## 28. Baselines

Required:

### B0 — Random same-count selection

Use deterministic seeds and 1000 repetitions per fold/policy unless runtime requires a documented reduction.

### B1 — Relative momentum rank

### B2 — Liquidity rank

### B3 — C7 absolute-return model rank

### B4 — C8 market-relative regression rank

Direct rank models must beat simpler alternatives to justify C10.

## 29. Statistical uncertainty

Required:

- deterministic date-block bootstrap;
- 95% CI for candidate outcome, spread and precision;
- fold dispersion;
- random-baseline distribution;
- empirical p-value versus random.

Suggested frozen defaults:

```text
block length = 5 sessions
bootstrap iterations = 2000
```

## 30. Policy selection

C9 may select at most:

```text
one primary policy
one conservative alternative
```

Required evidence:

```text
positive result in all 3 folds
positive aggregate 95% CI
not dominated by one year, sector, symbol or date cluster
stable across nearby thresholds
survives stronger liquidity screen
acceptable turnover relative to alternatives
supported by LightGBM and XGBoost
```

No C10 backtest may begin until policies are frozen.

## 31. Predefined policy candidates

### P1 — Broad canonical

```text
model: LightGBM
target: 5-session market-relative rank
features: B_market_context
selection: top 10%
rebalance: weekly first session
sector cap: 2
liquidity: canonical universe
```

### P2 — Conservative consensus

```text
models: LightGBM + XGBoost
selection: intersection of top 10%
rebalance: weekly first session
sector cap: 2
liquidity: top 75% turnover
```

### P3 — High conviction

```text
ensemble: average percentile rank
selection: top 5%
rebalance: non-overlapping 5-session
sector cap: 1
liquidity: top 50% turnover
```

These are candidates, not conclusions.

## 32. Signal Viewer compatibility

Generate summaries supporting filters for:

```text
model
ensemble
horizon
feature variant
selection policy
threshold
rebalance schedule
liquidity screen
sector constraint
fold
market regime
sector
```

Required visual datasets:

```text
outcome by threshold
precision/recall by k
selection spread
turnover timeline
retention curve
model overlap
sector and symbol concentration
regime and fold comparison
bootstrap intervals
random-baseline comparison
```

Updating the Signal Viewer itself is out of C9 scope.

## 33. Outputs

Suggested:

```text
data/processed/c9/
├── candidate_selections.parquet
├── candidate_outcomes.parquet
├── turnover_metrics.parquet
├── model_agreement.parquet
├── regime_metrics.parquet
├── concentration_metrics.parquet
├── baseline_metrics.parquet
└── viewer_summaries/
```

Required reports:

```text
artifacts/reports/C9_SELECTION_REPORT.md
artifacts/reports/C9_ROBUSTNESS_REPORT.md
artifacts/reports/C9_TURNOVER_REPORT.md
artifacts/reports/C9_MODEL_AGREEMENT_REPORT.md
artifacts/reports/C9_BASELINE_REPORT.md
artifacts/reports/C9_POLICY_DECISION.md
artifacts/reports/C9_DELIVERY.md
artifacts/reports/C9_MANIFEST.json
```

Required structured artifacts:

```text
artifacts/c9/selection_metrics.parquet
artifacts/c9/policy_metrics.parquet
artifacts/c9/bootstrap_metrics.parquet
artifacts/c9/viewer_summary.json
```

## 34. Manifest requirements

Record:

```text
manifest version
generation timestamp
branch and commit
dirty state
input and C8 prediction hashes
C8 manifest hash
models, target and feature sets
fold definitions
holdout access flag
policy, threshold, rebalance, liquidity and sector definitions
ensemble definitions
bootstrap settings
baseline seeds
row/date/symbol/sector and selection counts
fold, regime, concentration, turnover and agreement metrics
selected primary and conservative policies
output and logical hashes
runtime statistics
```

Timestamps must not affect logical hashes.

## 35. Suggested architecture

```text
src/psx_ml/c9/
├── inputs.py
├── policies.py
├── selection.py
├── outcomes.py
├── precision_metrics.py
├── turnover.py
├── persistence.py
├── liquidity.py
├── sector_constraints.py
├── concentration.py
├── model_agreement.py
├── ensemble.py
├── regimes.py
├── baselines.py
├── bootstrap.py
├── policy_decision.py
├── reports.py
├── manifest.py
└── pipeline.py
```

Suggested tests:

```text
tests/c9/
├── test_input_provenance.py
├── test_selection_thresholds.py
├── test_fixed_count_selection.py
├── test_percentile_selection.py
├── test_tie_handling.py
├── test_rebalance_schedules.py
├── test_holding_alignment.py
├── test_precision_metrics.py
├── test_turnover.py
├── test_persistence.py
├── test_liquidity_screens.py
├── test_sector_constraints.py
├── test_concentration.py
├── test_model_agreement.py
├── test_ensemble.py
├── test_regimes.py
├── test_random_baseline.py
├── test_bootstrap.py
├── test_holdout_lock.py
├── test_determinism.py
└── test_pipeline.py
```

## 36. Acceptance tests

### Repository and source safety

1. C9 runs only on `feature/c9-ranking-selection-robustness`.
2. Branch starts from accepted C8 on `main`.
3. Branch remains unmerged until explicit acceptance.
4. No SQLite access occurs.
5. `psx-stock-watcher` and `psx_watcher.db` remain unchanged.
6. C1–C8 artifacts are not overwritten.
7. Outputs outside the research repo are rejected.
8. Tests use temporary paths.

### Input and holdout safety

9. C8 hashes reconcile.
10. C8 folds remain authoritative.
11. Only out-of-fold predictions are used.
12. 2026 access fails by default.
13. Manifest records `holdout_accessed=false`.
14. Future-row append does not alter earlier selections.

### Selection correctness

15. Percentile selections match hand calculations.
16. Fixed-count selections match hand calculations.
17. Tie handling is deterministic.
18. Insufficient eligible-symbol cases are explicit.
19. Selection counts reconcile by date.
20. Bottom-tail direction is correct.
21. Rank thresholds are date-local.

### Rebalance and outcome alignment

22. Daily schedule is deterministic.
23. Two-session schedule is deterministic.
24. Weekly-first and weekly-last are calendar-correct.
25. Non-overlapping 5-session schedule is correct.
26. Future outcomes align with C8 target windows.
27. Overlapping and non-overlapping views remain separate.

### Metrics

28. Precision@k, recall@k and NDCG@k match hand calculations.
29. Top-decile capture and bottom-decile rejection reconcile.
30. Mean reciprocal rank is correct.
31. Candidate spread reconciles to row-level outcomes.
32. Bootstrap intervals are deterministic.

### Turnover and persistence

33. Retention and Jaccard overlap match hand calculations.
34. Entries and exits reconcile.
35. Gross turnover is deterministic.
36. Candidate lifetime is deterministic.
37. Rank persistence uses consecutive valid dates only.

### Liquidity and sector constraints

38. Liquidity screens are point-in-time.
39. Turnover ranks are date-local.
40. Sector caps of one and two are enforced.
41. Sector-neutral selection is correct.
42. Skipped and missing sectors are counted.

### Agreement and ensembles

43. Model rank correlation and overlap reconcile.
44. Average-rank ensemble is deterministic.
45. Consensus intersection and union are correct.
46. No learned ensemble weights are used.

### Concentration and robustness

47. Sector and symbol Herfindahl indexes are correct.
48. Top-date, top-symbol and top-sector contributions reconcile.
49. Leave-out diagnostics reconcile.
50. Fold, regime, threshold and rebalance results retain counts.

### Baselines

51. Random baseline preserves same-date count.
52. Random baseline is reproducible by seed.
53. Momentum and liquidity baselines are point-in-time.
54. C7/C8 model baselines reconcile.
55. Empirical p-values are correct.

### Policy decision

56. At most one primary and one conservative policy are selected.
57. Policies use predefined fixed rules.
58. No 2026 data influences selection.
59. Policies are not selected from aggregate metrics alone.
60. Nearby-threshold, liquidity, rebalance and concentration robustness are considered.
61. LightGBM/XGBoost agreement is reported.

### Provenance and delivery

62. Repeated runs produce identical logical hashes.
63. CPU-only C1–C9 suite passes.
64. GPU-specific verification passes.
65. Report generation occurs on a clean commit.
66. Manifest records correct commit and dirty state.
67. Viewer summaries are generated.
68. Report and structured-artifact counts reconcile.

### Scope

69. No fees, spread, slippage or market impact are introduced.
70. No portfolio accounting, Sharpe or drawdown is reported.
71. No profitability claim is made.
72. No live signal is generated.
73. No final-holdout result is reported.

## 37. Required implementation sequence

1. Confirm C8 is merged and tagged.
2. Create `feature/c9-ranking-selection-robustness` from updated `main`.
3. Freeze C9 configuration.
4. Validate C8 out-of-fold predictions and hashes.
5. Reconcile canonical C8 rank metrics.
6. Implement selection policies and schedules.
7. Implement outcome and ranking metrics.
8. Implement turnover and persistence.
9. Implement liquidity and sector constraints.
10. Implement concentration diagnostics.
11. Implement model agreement and fixed ensembles.
12. Implement regime and fold robustness.
13. Implement baselines and date-block bootstrap.
14. Run threshold, rebalance and liquidity sensitivity.
15. Run date, symbol and sector leave-out tests.
16. Compare LightGBM, XGBoost and ensemble variants.
17. Freeze primary and conservative C10 candidates.
18. Generate viewer summaries.
19. Run CPU suite with CUDA hidden.
20. Run GPU verification.
21. Commit implementation.
22. Regenerate reports and manifest from a clean commit.
23. Push branch for review.
24. Do not merge before acceptance.

## 38. Acceptance decision

C9 may be accepted even if no policy survives.

A positive result requires a fixed candidate rule that:

- is positive in all three folds;
- has a positive aggregate 95% CI;
- survives stronger liquidity filters;
- survives reasonable sector caps;
- is not driven by a few dates, symbols or sectors;
- is stable across nearby thresholds;
- is not destroyed by slower rebalancing;
- beats same-count random selection;
- compares favorably with simple momentum and liquidity baselines;
- is supported by LightGBM and XGBoost;
- leaves the 2026 holdout locked.

Final status must be one of:

```text
ACCEPT:
one primary and one conservative policy frozen for C10

ACCEPT WITH LIMITATIONS:
predictive selection exists only under narrow documented conditions

REJECT:
the C8 rank signal does not survive practical robustness tests
```

The key decision is:

> Does the five-session market-relative rank signal survive realistic selection, turnover, liquidity, concentration, regime and model-agreement tests strongly enough to justify a fee-aware C10 backtest?
