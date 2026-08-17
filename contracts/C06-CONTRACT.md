# C6 — Instrument Classification, Universe Refinement, and Robust Evaluation

## 1. Contract identity

- **Project:** `psx-ml-research`
- **Contract:** `C6_INSTRUMENT_CLASSIFICATION_UNIVERSE_REFINEMENT_AND_ROBUST_EVALUATION`
- **Required branch:** `feature/c6-universe-refinement-and-robust-evaluation`
- **Base:** accepted C5 merged into `main`
- **Purpose:** identify instrument types, refine the point-in-time research universe, quantify outlier and concentration effects, and establish robust evaluation variants before introducing nonlinear models.
- **Explicitly out of scope:** tree models, boosting, neural networks, model retraining on the final holdout, signal generation, portfolio construction, brokerage/fee modeling, execution simulation, backtesting, and profitability claims.

C6 must be implemented and reviewed on its own branch. It must not modify `psx-stock-watcher`, `psx_watcher.db`, or the pending watcher C14 branch.

## 2. Motivation

C5 produced a valid negative linear reference, but regression error was heavily concentrated in a small number of symbols/instruments. Before concluding that model nonlinearity is the missing ingredient, C6 must determine whether the research panel mixes ordinary equities with debt, government securities, funds, ETFs, REITs, rights, warrants, temporary listings, or other instrument types, and whether extreme rows are genuine equity moves or structural/data issues.

C6 must not remove rows merely because they worsen model metrics.

## 3. Source boundaries

C6 may read only research-owned artifacts inside `psx-ml-research`, including C1–C5 Parquet outputs, manifests, reports, predictions, coefficients, and repository documentation.

C6 must not:

- connect to SQLite at runtime;
- open or modify `psx_watcher.db`;
- overwrite C1–C5 outputs;
- silently scrape external websites during the pipeline;
- infer instrument type solely from ticker spelling when stronger metadata exists;
- apply today's classifications retrospectively without effective-date evidence.

Any external reference data added later must be stored as a versioned research-owned snapshot with provenance and effective-date semantics.

## 4. Instrument taxonomy

Suggested classes:

```text
ordinary_equity
preference_share
closed_end_fund
open_end_fund
ETF
REIT
debt_security
government_security
sukuk
commercial_paper
right_or_entitlement
warrant_or_option
index_or_non_security
temporary_or_special_listing
unknown
```

Every class must have a definition, evidence source, classification method, confidence/provenance, and effective dates where relevant.

### Evidence priority

1. explicit metadata already present in research artifacts;
2. versioned exchange/security-master metadata;
3. documented manually reviewed mapping;
4. deterministic ticker heuristic as a low-confidence fallback.

Heuristics must never be represented as authoritative metadata.

### Effective-dated classification

```text
symbol
effective_from
effective_to
instrument_type
classification_source
classification_confidence
```

Effective-date intervals for the same symbol must not overlap.

## 5. Canonical universe variants

### `pit_liquid_all_instruments_v1`

The existing C1/C3 PIT liquid universe, unchanged.

### `pit_liquid_ordinary_equity_v1`

Requires same-date C1 PIT liquidity eligibility and same-date `ordinary_equity` classification.

### `pit_liquid_equity_like_v1`

Optional broader universe including explicitly configured equity-like instruments such as REITs or preference shares.

### Diagnostic variants

Optional, separately named variants may test minimum price, minimum turnover, minimum listing age, persistent stale-series, or documented adjustment-anomaly rules. These are not retroactive edits to C1.

Every variant must record name/version, exact rule, row/symbol/date counts, exclusion reasons, and configuration hash.

## 6. Exclusion policy

C6 must distinguish:

```text
classification exclusion
data-quality exclusion
liquidity exclusion
history exclusion
diagnostic-only flag
```

Rows must not be excluded merely because returns or residuals are large, because a symbol worsens RMSE, because open/close lies outside high-low, or because the symbol later delisted.

Exclusion rules must be defined before comparing improved model metrics.

## 7. Outlier and concentration analysis

For each 5/10/20-session target, calculate:

```text
absolute target percentiles
squared-error contribution by symbol
absolute-error contribution by symbol
loss contribution by date
loss contribution by instrument type
top 1/5/10 symbol concentration
top 1/5/10 date concentration
largest individual residuals
```

Compare the all-instrument universe, ordinary-equity universe, optional equity-like universe, fixed C5 Ridge predictions, zero baseline, and training-mean baseline.

## 8. Extreme-return diagnostics

For extreme rows, report symbol, feature/entry/exit dates and prices, gross return, PIT eligibility, instrument type, listing age, liquidity and stale-history features, missing-history metadata, available adjustment-integrity flags, exact-session presence, low-price status, and special-instrument status.

Suggested reporting thresholds:

```text
absolute 5-session return > 50%
absolute 10-session return > 75%
absolute 20-session return > 100%
top 0.1% absolute target
top 0.1% squared residual
```

Thresholds are for diagnostics, not automatic deletion.

## 9. Robust evaluation variants

C6 re-evaluates accepted fixed C5 models or stored predictions. No new model family is introduced.

Required regression diagnostics:

```text
MAE
median absolute error
RMSE
trimmed RMSE diagnostic
Huber loss diagnostic
Pearson correlation
Spearman correlation
directional accuracy
date-level median error
```

Canonical untrimmed metrics must remain visible. Validation targets must not determine transformation thresholds.

Required cross-sectional diagnostics:

```text
daily Spearman IC
mean/median daily IC
IC standard deviation
positive-IC date fraction
top-minus-bottom prediction-quantile target spread
```

This is ranking evaluation only, not portfolio return.

Also report row-weighted, equal-date, equal-symbol diagnostic, and instrument-type-stratified results. Equal-symbol diagnostics must not silently become training weights.

Classification robustness must be reported by universe variant, instrument type, fold, year, horizon, liquidity bucket, and stale-history bucket.

The final holdout remains locked.

## 10. Universe recommendation rule

C6 may recommend a canonical C7 universe only if the rule is structurally justified, point-in-time safe, independent of residuals/targets, fully documented, sufficiently broad, stable across folds, and does not use the final holdout.

Better RMSE alone is not sufficient justification.

## 11. Outputs

Runtime outputs:

```text
data/processed/universe/c6_instrument_classification.parquet
data/processed/universe/c6_universe_membership.parquet
data/processed/diagnostics/c6_extreme_rows.parquet
data/processed/diagnostics/c6_loss_concentration.parquet
data/processed/diagnostics/c6_robust_metrics.parquet
```

Tracked artifacts:

```text
config/instruments.yaml
config/universe_c6.yaml
config/robust_evaluation.yaml
artifacts/reports/C6_INSTRUMENT_REPORT.md
artifacts/reports/C6_UNIVERSE_REPORT.md
artifacts/reports/C6_ROBUST_EVALUATION_REPORT.md
contracts/C06-DELIVERY.md
artifacts/reports/C6_MANIFEST.json
```

## 12. Manifest requirements

Record manifest version, generation timestamp, Git commit/dirty state, all input paths/hashes, taxonomy version, classification hierarchy, mapping/heuristic hashes, class counts, unknown counts, universe definitions, date/symbol counts, exclusions, thresholds, robust metric definitions, C5 prediction/model IDs, folds, holdout flag, per-universe metrics, concentration statistics, output hashes, logical hashes, and configuration hashes.

Generation timestamps must not affect logical hashes.

## 13. Reports

### Instrument report

Taxonomy, sources, class counts, unknowns, manual ambiguities, heuristic-only classifications, effective-date limitations, and examples of special instruments.

### Universe report

Universe variants, rules, row/symbol/date coverage, PIT behavior, exclusions, universe size by date, and recommended C7 universe with non-performance justification.

### Robust evaluation report

Original fixed C5 metrics, results by universe, robust diagnostics, concentration before/after justified refinement, stratified metrics, extreme-row examples, whether the negative linear conclusion changes, and explicit confirmation that no profitability evaluation occurred.

## 14. Suggested architecture

```text
src/psx_ml/
├── instruments/
│   ├── taxonomy.py
│   ├── classify.py
│   ├── mapping.py
│   ├── validation.py
│   ├── manifest.py
│   └── pipeline.py
├── universe/
│   ├── variants.py
│   ├── exclusions.py
│   ├── validation.py
│   └── c6_pipeline.py
├── diagnostics/
│   ├── extremes.py
│   ├── concentration.py
│   ├── robust_metrics.py
│   ├── stratification.py
│   └── pipeline.py
└── reporting/
    ├── instrument_report.py
    ├── universe_report.py
    └── robust_evaluation_report.py
```

GPU use is unnecessary.

## 15. Acceptance tests

1. Required C6 branch is used.
2. Runtime reads only research-owned artifacts.
3. Runtime makes zero SQLite connections.
4. Source DB and watcher fingerprints remain unchanged.
5. Tests use temporary outputs.
6. Outputs outside the repo are rejected.
7. C1–C5 outputs are never overwritten.
8. Every classification uses a valid taxonomy value.
9. Unknowns remain explicit.
10. Explicit metadata overrides heuristics.
11. Manual mappings override heuristics and are version-hashed.
12. Heuristics retain low-confidence provenance.
13. Effective-date intervals do not overlap.
14. Classification is input-order invariant.
15. Current classifications are not applied retrospectively without evidence.
16. Class counts reconcile.
17. Original C1 PIT eligibility is unchanged.
18. Ordinary-equity membership requires same-date PIT eligibility and same-date class.
19. Ineligible rows cannot enter refined universes.
20. Today’s classifications are not incorrectly applied historically.
21. Exclusion reasons are deterministic.
22. Residual magnitude is never an exclusion input.
23. Target values are never exclusion inputs.
24. Universe membership is invariant to C5 prediction changes.
25. Date-level counts reconcile.
26. Symbol-level counts reconcile.
27. Appending future rows cannot alter earlier membership.
28. Symbol squared-loss shares sum to one within scope.
29. Date loss shares sum to one within scope.
30. Top-N concentration matches hand calculations.
31. Extreme thresholds are deterministic.
32. Open/close outside high-low does not automatically invalidate rows.
33. Missing exact entry/exit observations remain distinguishable.
34. Instrument-type loss aggregation reconciles.
35. Unaffected-symbol diagnostics are isolated from other symbols.
36. Original fixed C5 metrics reproduce within tolerance.
37. Robust metrics match hand examples.
38. Median absolute error is correct.
39. Trimmed metrics retain untrimmed metrics.
40. Validation targets do not set transformation thresholds.
41. Daily IC uses same-date valid eligible rows only.
42. Daily IC minimum population is enforced.
43. Quantile ties are deterministic.
44. Equal-date metrics do not weight by universe size.
45. Instrument-type metrics reconcile.
46. Final holdout remains locked and `holdout_accessed=false`.
47. Changing holdout data cannot alter development metrics.
48. Repeated runs produce identical logical hashes.
49. Manifest hashes reconcile.
50. Reports distinguish structural exclusions from diagnostics.
51. Any C7 universe recommendation has non-performance justification.
52. Negative linear findings remain visible.
53. No nonlinear model, signal, fee model, portfolio, execution, or backtest is introduced.
54. No profitability claim is made.
55. Full C1–C6 suite passes with CUDA hidden.
56. Watcher C14 remains untouched.

## 16. Required implementation sequence

1. Confirm C5 is merged and tagged.
2. Create `feature/c6-universe-refinement-and-robust-evaluation` from updated `main`.
3. Inspect actual symbol metadata in C1–C5 artifacts.
4. Define taxonomy and evidence hierarchy.
5. Build and test classification output.
6. Build PIT-safe universe variants.
7. Reconcile counts and exclusions.
8. Implement extreme-row and concentration diagnostics.
9. Reproduce fixed C5 metrics.
10. Add robust and stratified evaluation.
11. Recommend or reject a refined C7 universe.
12. Generate manifests and reports.
13. Run complete CPU-only C1–C6 suite.
14. Produce delivery evidence.
15. Do not merge before acceptance.

## 17. Acceptance decision

C6 may be accepted only when instrument classes and unknowns are explicit, universe variants are point-in-time safe, exclusions are structural rather than performance-driven, C5 loss concentration is explained quantitatively, robust metrics are reproducible, the final holdout remains locked, no nonlinear model/backtest enters scope, and production sources remain unchanged.

C6 should establish whether C7 is testing nonlinearity on a trustworthy equity universe rather than asking a stronger model to learn around mixed instrument types and avoidable data pathologies.
