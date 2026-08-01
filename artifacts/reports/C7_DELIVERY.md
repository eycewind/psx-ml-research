# C7 Corrective Delivery and Acceptance Report

## Correction outcome

The earlier LightGBM daily-IC `NaN` values came from a legacy helper admitting
undefined same-date Spearman correlations and ordinary fold means propagating
those non-finite values. C7 now checks population, target variation, prediction
variation, and correlation finiteness separately. Undefined IC is excluded from
IC statistics and is never coerced to zero. Each reason and eligible-date count
is retained in the manifest and model report.

## Finite LightGBM IC dates

The model report contains the complete task/model/fold table, including Hist,
XGBoost and baselines. Canonical LightGBM finite/eligible counts are:

| Target | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| 5-session regression | 182/246 | 246/246 | 67/250 |
| 10-session regression | 185/246 | 246/246 | 218/250 |
| 20-session regression | 120/246 | 246/246 | 250/250 |

Constant naive predictions correctly have zero finite IC dates. Undefined dates
remain visible through `constant_prediction_date_count`,
`constant_target_date_count`, and `nonfinite_ic_date_count`.

## One-round diagnosis

Every task/model/fold now records prediction/probability distribution statistics,
rounded unique counts, a near-constant flag, best iteration, metric, best inner
score, first score, and last evaluated iteration. Models selected at one or two
rounds produced 6–294 unique rounded predictions and prediction standard
deviations from 0.000789 to 0.00552. None was flagged constant or near-constant.
The best score occurred at iteration 1–2 and evaluation continued through the
30-round patience window. This supports legitimate inner-period regime or
generalization failure rather than a constant-prediction pipeline defect.

## Verification and provenance

- CPU suite: `CUDA_VISIBLE_DEVICES="" python -m pytest -s` — 70 passed,
  1 GPU test skipped.
- C7 CUDA test: 1 passed on the RTX 5070 Laptop GPU.
- Regenerated validation rows: 5,324,172.
- Generation commit: `8b229d62a6b7eba15eee12ee3ebb5d8ee5eb529f`.
- Generation manifest: `dirty = false`, `holdout_accessed = false`.

## Decision

The correction improves the accuracy and auditability of daily-IC reporting but
does not change the C7 conclusion. Nonlinear predictive structure remains weak
and unstable, classification loss generally does not improve on prevalence, and
C7 does not establish a practical model or profitability result. The 2026 final
holdout remains locked.
