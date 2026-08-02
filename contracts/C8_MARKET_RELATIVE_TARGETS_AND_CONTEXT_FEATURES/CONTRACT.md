# C8 — Market-Relative Targets and Market/Sector Context Features

## 1. Contract identity

- **Project:** `psx-ml-research`
- **Contract:** `C8_MARKET_RELATIVE_TARGETS_AND_CONTEXT_FEATURES`
- **Required branch:** `feature/c8-market-relative-targets-and-context`
- **Base:** accepted C7 merged into `main`
- **Canonical universe:** `pit_liquid_ordinary_equity_v1`
- **Primary horizons:** 5 and 10 sessions
- **Secondary diagnostic horizon:** 20 sessions
- **Purpose:** determine whether the weak and unstable ranking structure found in C7 becomes more stable when the prediction problem is reframed around market-relative and sector-relative performance and when the model receives richer point-in-time market and sector context.
- **Primary model:** LightGBM CPU
- **Independent verification model:** XGBoost GPU
- **Reference model:** HistGradientBoosting CPU
- **Final holdout:** remains locked

C8 must be implemented and reviewed on its own branch. It must not modify `psx-stock-watcher`, `psx_watcher.db`, the accepted Signal Viewer implementation, or the pending watcher C14 branch.

---

## 2. Motivation

C7 showed:

- weak but nonzero ranking structure at 5–10 sessions;
- stronger results in some folds than others;
- weaker 20-session behavior;
- unstable feature importance;
- strong variation in selected boosting rounds across folds;
- prediction-bucket means that often reflected overall market direction rather than clean stock-selection skill.

The current absolute-return target combines:

```text
future stock return
=
market movement
+ sector movement
+ stock-specific movement
```

C8 separates these components and asks a cleaner question:

> Which stocks are likely to outperform or underperform the market or their sector over the next 5–10 sessions?

C8 must not assume that relative targets will work. A negative result is acceptable if the implementation is correct.

---

## 3. Scope

### In scope

- point-in-time market benchmark construction;
- point-in-time sector benchmark construction;
- market-relative targets;
- sector-relative targets;
- cross-sectional rank targets;
- new market-context features;
- new sector-context features;
- stock-relative features;
- walk-forward evaluation using accepted C4 folds;
- comparison against C7 absolute-return results;
- prediction-bucket and daily-IC diagnostics;
- feature ablation;
- stability analysis;
- Signal Viewer-compatible structured outputs.

### Out of scope

- trading signals;
- buy/sell rules;
- position sizing;
- portfolio construction;
- transaction costs;
- brokerage;
- spread;
- slippage;
- execution simulation;
- backtesting;
- Sharpe ratio;
- P&L;
- profitability claims;
- news ingestion;
- deep learning;
- direct use of the final 2026 holdout.

---

## 4. Source boundaries

C8 may read only research-owned artifacts and accepted reference data.

Expected inputs include:

```text
data/processed/features/daily_features.parquet
data/processed/targets/daily_feature_targets.parquet
data/processed/datasets/temporal_split_assignments.parquet
data/processed/universe/c6_universe_membership.parquet
data/reference/psx_security_master_2026-08-01.parquet
artifacts/predictions/c7/
artifacts/reports/C3_*.json
artifacts/reports/C4_*.json
artifacts/reports/C6_*.json
artifacts/reports/C7_*.json
config/
```

C8 must not:

- connect to SQLite;
- read `psx_watcher.db`;
- modify production watcher code;
- use live APIs during feature generation or evaluation;
- overwrite C1–C7 outputs;
- use final-holdout data;
- use future values in feature construction;
- use current PSX classifications as if they were historical point-in-time truth without preserving the documented backcast limitation.

---

## 5. Canonical universe

C8 canonical rows must satisfy:

```text
universe_name = pit_liquid_ordinary_equity_v1
point_in_time_eligible = true
valid C4 fold assignment
valid target for selected horizon
```

The canonical universe remains broad ordinary equity.

Sector-relative targets may only be computed where a valid sector assignment exists.

Rows lacking valid sector membership must:

- remain available for market-relative tasks;
- be excluded from sector-relative tasks;
- be counted explicitly;
- never receive an imputed sector benchmark.

---

## 6. Benchmark definitions

C8 must build benchmark series from the research universe using only information available on each date.

### 6.1 Market benchmark

Required canonical benchmark:

```text
market_cross_sectional_median_return
```

For each trading date and horizon, calculate the median future return across eligible ordinary equities.

Optional secondary benchmark:

```text
market_equal_weight_mean_return
```

If an external KSE-100 series already exists as an accepted point-in-time research artifact, it may be added as a secondary benchmark. It must not be fetched live during C8.

### 6.2 Sector benchmark

Required canonical benchmark:

```text
sector_cross_sectional_median_return
```

For each trading date, sector, and horizon, calculate the median future return across eligible ordinary equities in the same sector.

Minimum sector population must be configurable and explicit.

Suggested default:

```text
minimum_sector_symbols = 5
```

If the sector has fewer than the required symbols on a date, the sector-relative target is invalid for that row.

### 6.3 Leave-one-out requirement

The stock being evaluated must not contribute to its own market or sector benchmark.

Required:

```text
leave-one-out market benchmark
leave-one-out sector benchmark
```

This prevents mechanical target contamination.

### 6.4 Benchmark weighting

Canonical benchmarks must be equal-weighted or median-based.

C8 must not introduce market-cap weighting unless a valid point-in-time market-cap series exists.

---

## 7. Target definitions

### 7.1 Existing absolute-return targets

Retain for comparison:

```text
fwd_open_to_close_ret_5s_adj
fwd_open_to_close_ret_10s_adj
fwd_open_to_close_ret_20s_adj
```

### 7.2 Market-relative regression targets

Required:

```text
fwd_market_relative_ret_5s
fwd_market_relative_ret_10s
fwd_market_relative_ret_20s
```

Definition:

```text
stock future return
-
leave-one-out market benchmark future return
```

### 7.3 Sector-relative regression targets

Required:

```text
fwd_sector_relative_ret_5s
fwd_sector_relative_ret_10s
fwd_sector_relative_ret_20s
```

Definition:

```text
stock future return
-
leave-one-out sector benchmark future return
```

### 7.4 Cross-sectional rank targets

Required:

```text
fwd_market_relative_rank_5s
fwd_market_relative_rank_10s
fwd_market_relative_rank_20s
```

Ranks must be computed within the same trade date using only eligible rows with valid targets.

Required rank convention:

```text
0.0 = lowest future relative return
1.0 = highest future relative return
```

Ties must be deterministic.

### 7.5 Relative classification targets

Required:

```text
outperform_market_5s
outperform_market_10s
outperform_market_20s

outperform_sector_5s
outperform_sector_10s
outperform_sector_20s
```

Definition:

```text
1 if relative return > 0
0 otherwise
```

Optional tail classification:

```text
top_decile_market_relative_5s
top_decile_market_relative_10s
bottom_decile_market_relative_5s
bottom_decile_market_relative_10s
```

Tail labels must be computed by date and must not use future dates.

---

## 8. Point-in-time market-context features

All features must use current and past observations only.

Required market features:

```text
market_median_ret_1obs
market_median_ret_5obs
market_median_ret_10obs
market_median_ret_20obs

market_mean_ret_1obs
market_mean_ret_5obs
market_mean_ret_10obs
market_mean_ret_20obs

market_breadth_positive_1obs
market_breadth_positive_5obs
market_breadth_above_20obs_mean

market_advance_decline_ratio_1obs
market_advance_decline_ratio_5obs

market_cross_sectional_dispersion_1obs
market_cross_sectional_dispersion_5obs
market_cross_sectional_dispersion_20obs

market_realized_volatility_5obs
market_realized_volatility_20obs

market_turnover_median_1obs
market_turnover_median_20obs

eligible_symbol_count
eligible_symbol_count_change_5obs
```

Definitions must be explicit and versioned.

No benchmark feature may include future returns.

---

## 9. Point-in-time sector-context features

Required sector features:

```text
sector_median_ret_1obs
sector_median_ret_5obs
sector_median_ret_10obs
sector_median_ret_20obs

sector_breadth_positive_1obs
sector_breadth_positive_5obs

sector_cross_sectional_dispersion_1obs
sector_cross_sectional_dispersion_20obs

sector_realized_volatility_5obs
sector_realized_volatility_20obs

sector_turnover_median_20obs
sector_eligible_symbol_count
```

Sector features must use leave-one-out construction where the stock’s own value would otherwise mechanically affect the benchmark.

If a sector/date does not meet minimum population:

- sector features become null;
- no cross-sector fallback is allowed;
- missingness must remain explicit.

---

## 10. Stock-relative features

Required:

```text
stock_minus_market_ret_1obs
stock_minus_market_ret_5obs
stock_minus_market_ret_20obs

stock_minus_sector_ret_1obs
stock_minus_sector_ret_5obs
stock_minus_sector_ret_20obs

stock_market_relative_rank_1obs
stock_market_relative_rank_5obs
stock_market_relative_rank_20obs

stock_sector_relative_rank_1obs
stock_sector_relative_rank_5obs
stock_sector_relative_rank_20obs

rolling_beta_market_60obs
rolling_corr_market_60obs
rolling_beta_sector_60obs
rolling_corr_sector_60obs
```

Minimum observation requirements must be explicit.

Suggested:

```text
minimum rolling observations = 30
maximum rolling window = 60
```

---

## 11. Feature-set variants

C8 must compare controlled feature families.

### Variant A — C7 baseline

```text
existing frozen 27 C3 features
```

### Variant B — C7 + market context

```text
27 C3 features
+ market-context features
+ stock-market-relative features
```

### Variant C — C7 + sector context

```text
27 C3 features
+ sector-context features
+ stock-sector-relative features
```

### Variant D — Full context

```text
27 C3 features
+ market context
+ sector context
+ stock-relative features
```

### Variant E — Context only

```text
market context
+ sector context
+ stock-relative features
```

This variant tests whether new features carry independent information.

Feature variants must be fixed before canonical evaluation.

---

## 12. Model stack

### Required models

```text
HistGradientBoosting CPU reference
LightGBM deterministic CPU primary
XGBoost GPU independent verification
```

Do not introduce new model families in C8 unless separately justified.

C8 should reuse accepted C7 model infrastructure where possible.

### Hyperparameters

C8 is not a broad tuning contract.

Use:

- accepted C7 configurations as the starting point;
- a small fixed candidate set only where target scale or class balance requires adjustment;
- leakage-safe sequential or nested selection;
- early stopping using train-internal chronology.

No large random search, Bayesian optimization, or thousands of trials.

---

## 13. Evaluation design

### 13.1 Folds

Use accepted C4 folds:

```text
fold_2023
fold_2024
fold_2025
```

For each fold:

- fit only training rows;
- use only permitted train-internal data for early stopping;
- score only same-fold validation rows;
- preserve date-level split integrity;
- exclude purged, embargoed, test, and not-in-fold rows.

### 13.2 Final holdout

The 2026 holdout remains locked.

Any direct or indirect use must fail unless explicitly authorized by a later contract.

Manifest requirement:

```text
holdout_accessed = false
```

### 13.3 Canonical comparison matrix

At minimum, compare:

```text
absolute target + Variant A
absolute target + Variant D

market-relative target + Variant A
market-relative target + Variant B
market-relative target + Variant D

sector-relative target + Variant A
sector-relative target + Variant C
sector-relative target + Variant D

rank target + Variant B
rank target + Variant D
```

Not every model must run every exploratory combination if runtime becomes excessive, but the canonical LightGBM comparison matrix must be complete.

---

## 14. Metrics

### 14.1 Regression

Required:

```text
MAE
median absolute error
RMSE
R²
Pearson
Spearman
mean daily IC
median daily IC
daily IC standard deviation
positive-IC-date fraction
quantile spread
top-2 minus bottom-2 bucket spread
D10 minus D1 mean spread
D10 minus D1 median spread
```

### 14.2 Ranking

Required:

```text
mean daily Spearman IC
median daily IC
positive-date fraction
NDCG@5
NDCG@10
top-decile capture
bottom-decile capture
bucket monotonicity score
```

If NDCG is used, relevance mapping must be explicit and deterministic.

### 14.3 Classification

Required:

```text
ROC AUC
PR AUC
log loss
Brier score
balanced accuracy
precision
recall
F1
calibration bins
prevalence
```

### 14.4 Stability

Required by:

```text
fold
validation year
horizon
target family
feature variant
model
liquidity bucket
sector
market regime
```

All subgroup rows must report counts.

### 14.5 Uncertainty

Required:

- deterministic date-block bootstrap;
- 95% interval for mean daily IC;
- 95% interval for D10-D1 spread;
- fold dispersion;
- finite/undefined IC date counts.

Undefined IC must never be coerced to zero.

---

## 15. Market-regime diagnostics

C8 must define point-in-time diagnostic regimes.

Suggested regimes:

```text
market trend:
    positive / neutral / negative

market volatility:
    low / medium / high

market breadth:
    narrow / neutral / broad

cross-sectional dispersion:
    low / medium / high
```

Regime thresholds must be based on training-period quantiles only.

C8 must first use regimes as diagnostics and features.

Separate regime-specific models are out of scope unless a later contract authorizes them.

---

## 16. Prediction-bucket analysis

For every canonical regression/rank task:

- assign date-wise prediction buckets;
- default to 10 buckets;
- retain 5-bucket and 20-bucket options;
- use deterministic tie handling;
- report bucket row/date/symbol counts;
- report mean and median target per bucket;
- report bootstrap intervals;
- report D10-D1 and top-2-minus-bottom-2 spread;
- report monotonicity score;
- preserve fold-level views.

A positive market does not by itself indicate model skill.

The key question is:

```text
Do higher predicted buckets consistently outperform lower predicted buckets?
```

---

## 17. Feature ablation

Required ablations:

```text
remove all market-context features
remove all sector-context features
remove all stock-relative features
remove eligible_symbol_count
remove market_median_ret_1obs_adj
```

For each ablation, report:

```text
change in mean daily IC
change in quantile spread
change in fold dispersion
change in selected rounds
change in feature-importance stability
```

Ablation decisions must be evaluated on earlier evidence and tested forward.

---

## 18. Leakage controls

Required protections:

1. future benchmark returns cannot enter features;
2. target benchmark construction uses future returns only in target-generation code;
3. feature benchmark construction uses current/past returns only;
4. stock is excluded from its own benchmark;
5. validation rows cannot affect training-period regime thresholds;
6. validation rows cannot affect feature normalization;
7. sector membership is date-valid where possible and provenance is retained;
8. final holdout cannot affect any feature, threshold, target, or report;
9. cross-sectional ranks are computed within the same date only;
10. target columns cannot enter the feature matrix.

---

## 19. Sanity tests

Required:

1. leave-one-out market benchmark matches hand calculation;
2. leave-one-out sector benchmark matches hand calculation;
3. single-member sector produces invalid sector-relative target;
4. minimum sector population is enforced;
5. date-wise rank boundaries are correct;
6. tied ranks are deterministic;
7. market-relative targets center as expected under the selected benchmark;
8. sector-relative targets center within sector/date where mathematically expected;
9. shuffled targets destroy performance;
10. future-row append does not alter earlier features;
11. changing validation targets does not alter training;
12. relative features use only past/current returns;
13. regime thresholds are fit on training rows only;
14. prediction buckets reconcile to row-level predictions;
15. D10-D1 spread reconciles to bucket output;
16. undefined IC handling remains correct.

---

## 20. Practical-use decision criteria

C8 may be called promising only if the relative-target/context design improves stability, not just average performance.

Required evidence should include most of:

```text
positive mean daily IC
positive IC in at least 2 of 3 folds
smaller fold dispersion than C7
positive D10-D1 spread in at least 2 of 3 folds
95% interval excluding zero for selected canonical metric
better performance than same-model absolute-target baseline
improvement over naive and C7 baselines
no one-year-only effect
no dependence on a single sector
feature importance more stable than C7
```

A model must not be called practical based only on:

- one strong fold;
- one positive aggregate metric;
- one strong bucket;
- better RMSE with weak ranking;
- post hoc target or feature selection.

---

## 21. Outputs

Suggested runtime outputs:

```text
data/processed/targets/c8_relative_targets.parquet
data/processed/features/c8_market_context_features.parquet
data/processed/features/c8_sector_context_features.parquet
data/processed/features/c8_relative_features.parquet
data/processed/model_inputs/c8/
data/processed/diagnostics/c8/

artifacts/predictions/c8/
artifacts/models/c8/
```

Required tracked reports:

```text
artifacts/reports/C8_TARGET_REPORT.md
artifacts/reports/C8_FEATURE_REPORT.md
artifacts/reports/C8_MODEL_REPORT.md
artifacts/reports/C8_BUCKET_REPORT.md
artifacts/reports/C8_ABLATION_REPORT.md
artifacts/reports/C8_DELIVERY.md
artifacts/reports/C8_MANIFEST.json
```

---

## 22. Signal Viewer compatibility

C8 outputs must support the existing ML Model Analysis UI.

Required API-ready datasets must allow:

```text
absolute vs market-relative vs sector-relative comparison
feature-variant comparison
daily IC timeline
fold comparison
prediction buckets
confidence intervals
feature-importance stability
training diagnostics
market-regime filtering
sector filtering
```

C8 must not require loading full prediction files into the browser.

Structured summaries should be generated in Parquet or JSON for efficient read-only API access.

---

## 23. Manifest requirements

Record:

```text
manifest version
generation timestamp
Git commit
dirty state
input hashes
C3 feature manifest hash
C4 split manifest hash
C6 universe manifest hash
C7 model manifest hash
benchmark definitions
leave-one-out policy
sector minimum population
target definitions
feature definitions
ordered feature variants
model/library versions
hyperparameters
selection strategy
early-stopping policy
fold/date ranges
holdout access flag
row/date/symbol counts
sector coverage counts
missing-sector counts
per-fold metrics
aggregate metrics
bootstrap intervals
bucket metrics
ablation metrics
prediction hashes
feature hashes
target hashes
model hashes
logical-content hashes
runtime statistics
```

Generation timestamps must not affect logical hashes.

---

## 24. Suggested architecture

```text
src/psx_ml/c8/
├── benchmarks.py
├── relative_targets.py
├── market_features.py
├── sector_features.py
├── relative_features.py
├── feature_variants.py
├── regimes.py
├── datasets.py
├── train.py
├── metrics.py
├── buckets.py
├── ablation.py
├── reports.py
├── manifest.py
└── pipeline.py
```

Suggested tests:

```text
tests/c8/
├── test_market_benchmark.py
├── test_sector_benchmark.py
├── test_leave_one_out.py
├── test_relative_targets.py
├── test_rank_targets.py
├── test_market_features.py
├── test_sector_features.py
├── test_relative_features.py
├── test_feature_variants.py
├── test_regimes.py
├── test_fold_isolation.py
├── test_holdout_lock.py
├── test_bucket_metrics.py
├── test_ablation.py
├── test_determinism.py
└── test_pipeline.py
```

---

## 25. Acceptance tests

### Repository and source safety

1. C8 runs only on `feature/c8-market-relative-targets-and-context`.
2. No SQLite connection is made.
3. Production DB and watcher repository remain unchanged.
4. C1–C7 outputs are never overwritten.
5. Tests use temporary paths.
6. Outputs outside the research repository are rejected.

### Universe and benchmark construction

7. Canonical rows belong to `pit_liquid_ordinary_equity_v1`.
8. Market benchmark uses only same-date valid eligible equities.
9. Sector benchmark uses only same-date valid same-sector equities.
10. Stock is excluded from its own benchmark.
11. Sector minimum population is enforced.
12. Missing sector benchmark remains null.
13. Benchmark calculations are deterministic.
14. Future benchmark values do not enter features.

### Targets

15. Market-relative targets match hand calculations.
16. Sector-relative targets match hand calculations.
17. Rank targets are date-local and deterministic.
18. Tail labels use same-date ranks only.
19. Invalid target rows are explicitly counted.
20. Appending future rows does not alter earlier targets.

### Features

21. Market features use only current/past observations.
22. Sector features use only current/past observations.
23. Relative features use leave-one-out benchmarks where required.
24. Rolling beta/correlation minimum history is enforced.
25. Feature order is fixed and versioned.
26. Missing sector context remains explicit.
27. Future-row append does not alter earlier features.

### Fold and holdout safety

28. C4 folds remain authoritative.
29. Only train rows are fitted.
30. Only same-fold validation rows are scored.
31. Purged/embargoed/test/not-in-fold rows are excluded.
32. Validation data does not define regime thresholds.
33. Current validation does not select its own hyperparameters.
34. Final holdout access fails by default.
35. Manifest records `holdout_accessed=false`.

### Models and metrics

36. C7 baseline metrics reproduce where expected.
37. Relative-target models train deterministically within tolerance.
38. Regression metrics match hand calculations.
39. Ranking metrics match hand calculations.
40. Daily IC uses finite same-date values only.
41. Undefined IC reasons are counted.
42. Prediction buckets reconcile to predictions.
43. D10-D1 and top-2-bottom-2 spreads reconcile.
44. Bucket monotonicity is deterministic.
45. Bootstrap intervals are deterministic.
46. Fold dispersion is retained.
47. Sector and regime subgroup counts reconcile.

### Ablation and robustness

48. Market-feature ablation removes only intended features.
49. Sector-feature ablation removes only intended features.
50. Stock-relative ablation removes only intended features.
51. Shuffled targets destroy performance.
52. Noise features do not produce stable gain.
53. No single sector dominates canonical performance without being reported.
54. No single year dominates canonical performance without being reported.

### Provenance and delivery

55. Repeated CPU runs produce identical logical hashes.
56. GPU verification reproduces within documented tolerance.
57. Input and output hashes are recorded.
58. Git commit and dirty state are recorded.
59. CPU-only C1–C8 suite passes.
60. C8 GPU-specific tests pass.
61. Signal Viewer summary artifacts are generated.
62. Pending watcher C14 remains untouched.

### Scope

63. No signal generation is introduced.
64. No fee or execution logic is introduced.
65. No portfolio or backtest is introduced.
66. No profitability claim is made.
67. No final-holdout result is reported.

---

## 26. Required implementation sequence

1. Confirm C7 is merged and tagged.
2. Create `feature/c8-market-relative-targets-and-context` from updated `main`.
3. Freeze benchmark definitions and sector minimum population.
4. Implement leave-one-out market benchmark.
5. Implement leave-one-out sector benchmark.
6. Implement relative regression targets.
7. Implement rank and outperform targets.
8. Implement market-context features.
9. Implement sector-context features.
10. Implement stock-relative features.
11. Implement feature variants.
12. Add leakage and determinism tests.
13. Reproduce C7 baselines.
14. Run LightGBM canonical comparison matrix.
15. Run XGBoost GPU verification.
16. Run HistGradientBoosting reference.
17. Generate bucket, confidence, regime, and sector diagnostics.
18. Run feature ablations.
19. Generate Signal Viewer-compatible summaries.
20. Run complete CPU-only C1–C8 suite.
21. Run GPU-specific tests.
22. Generate reports and manifest from a clean committed state.
23. Do not merge before acceptance.

---

## 27. Acceptance decision

C8 may be accepted even if relative targets and context features fail.

A positive C8 result requires evidence that:

- market-relative or sector-relative targets improve ranking stability;
- improvements persist across folds;
- prediction buckets show cleaner separation;
- confidence intervals support the effect;
- gains are not driven by one year or sector;
- feature importance is at least somewhat more stable than C7;
- the final 2026 holdout remains locked.

C8 is a predictive research contract, not a trading-strategy contract.

The key decision is:

> Does removing broad market/sector movement from the target and adding point-in-time market/sector context produce a more stable stock-selection signal than C7?
