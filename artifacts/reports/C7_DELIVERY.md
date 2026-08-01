# C7 Delivery and Acceptance Report

## Outcome

C7 implemented and executed the locked walk-forward evaluation on
`pit_liquid_ordinary_equity_v1`. The 2026 final holdout was not accessed.

The nonlinear models show weak predictive structure, but not a sufficiently
stable practical result. XGBoost produced the strongest ranking diagnostics at
5 and 10 sessions; performance weakened materially at 20 sessions. The primary
LightGBM configuration often stopped after very few rounds and did not establish
stable superiority to naive baselines. No profitability claim is made.

## Delivered

- HistGradientBoosting CPU regression and classification reference models.
- Deterministic LightGBM CPU models with chronological train-internal early
  stopping and sequential walk-forward candidate selection.
- Independent XGBoost CUDA verification on the RTX 5070 Laptop GPU.
- Frozen ordered 27-feature C3 allowlist and native missing-value handling.
- C5 fixed baselines re-evaluated on the canonical C7 universe.
- Per-fold robust regression, ranking, classification, calibration, date-block
  uncertainty, feature-importance, and runtime evidence.
- Deterministically sorted validation predictions and feature importance.

## Acceptance evidence

- Focused tests: `5 passed`.
- Validation prediction rows: `5,324,172`.
- Validation dates: `742`; symbols: `367`.
- Feature-importance rows: `972`.
- `holdout_accessed = false` in the manifest.
- LightGBM fold 2024 uses only 2023 selection evidence; fold 2025 uses only
  2023–2024 evidence. Current outer validation is never early-stopping data.
- XGBoost executed with `tree_method=hist`, `device=cuda`.

## Limitations and decision

The C6 current-master historical-backcast limitation remains. Aggregate positive
correlations alone do not establish stability: fold dispersion is meaningful,
20-session results are weak, and classification loss generally does not improve
on the prevalence baseline. C7 therefore does **not** establish a practical
model and should not proceed directly to trading-rule or profitability claims.

The final 2026 holdout remains locked for a later explicitly authorized stage.
