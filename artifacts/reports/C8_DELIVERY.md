# C8 Delivery Report

Generation commit: `19effafc90c6ccf338535a9400fee5bcc11a30b3`; dirty: **False**; holdout accessed: **False**.

Prediction rows: **9850632**; fitted model/task/fold combinations: **216**.

## Conclusion

C8 upgrades the conclusion from weak and unstable C7 evidence to qualified positive evidence for five-session market-relative prediction, especially for LightGBM using the unchanged C7 feature set. Its aggregate daily-IC and D10-D1 intervals exclude zero, and CUDA XGBoost corroborates the sign. Broader context features do not consistently improve this result. Shrunk sector targets improve coverage and show positive natural and strict-matched evidence at five sessions, but context-feature and importance-stability gains are mixed. This is promising predictive evidence, not evidence of implementable profitability or authorization to unlock 2026.

## Canonical C8 result

- Target: five-session market-relative return (`fwd_market_relative_ret_5s`).
- Model: LightGBM CPU.
- Features: `A_c7_only` (unchanged C7 feature set).
- Mean daily IC: `0.0507703`; positive folds: `3/3`.
- Mean D10-D1: `0.00854297`; positive D10-D1 folds: `3/3`.
- The 2026 holdout is untouched.

Broader context features did not consistently improve this canonical result.

## Key evidence

- Market-relative 5-session LightGBM A: mean daily IC `0.0507703` versus absolute A `0.0221228`; positive IC folds `3/3`; positive D10-D1 folds `3/3`.
- Shrunk sector 5-session LightGBM C: natural mean IC `0.0485837`; strict-matched mean IC `0.0444205`.
- 2023 and 2025 remain positive for the selected five-session market-relative result; the result is not a 2024-only effect.
- No fitted model was flagged near-constant.

No trade rules, fees, portfolio logic, backtest, or profitability claim is part of C8.

## Verification

{
  "c8_gpu_suite": "1 passed, 1 warning (C8 XGBoost CUDA)",
  "cpu_suite": "92 passed, 3 skipped (CUDA hidden)"
}

## Remaining contract matrix

Direct rank-target and relative-classification models were added from clean commit `e8e63d660f7bd90f18bcbc722e1df1e9b349053e`. They add **48** fitted models and **2226020** validation predictions. Five-session rank/B LightGBM mean daily IC is `0.108729` with fold ICs `[0.09931942323554063, 0.10297823605625356, 0.12388813128392143]`. Five-session market-outperformance LightGBM ROC AUC is `0.555213` versus `0.5` for the prevalence baseline. Full rank, NDCG, capture, spread, classification, calibration, and fold-stability results are in C8_MODEL_REPORT.md and the structured supplemental artifact. The 2026 holdout remained untouched.
