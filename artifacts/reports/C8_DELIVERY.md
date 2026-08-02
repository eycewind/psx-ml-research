# C8 Delivery Report

Generation commit: `e79bf855dfc9ef8a915363d3e0cad1b0e81d55d3`; dirty: **False**; holdout accessed: **False**.

Prediction rows: **9850632**; fitted model/task/fold combinations: **216**.

## Conclusion

C8 changes the research conclusion from C7's negative absolute-return result to a qualified positive result for target reframing: five-session market-relative LightGBM with the unchanged C7 features is positive in all folds, its aggregate daily-IC and D10-D1 intervals exclude zero, and CUDA XGBoost corroborates the sign. New context features do not consistently improve market-relative models. Shrunk sector targets improve coverage and show positive natural and strict-matched evidence at five sessions, but context-feature and importance-stability gains are mixed. This is promising predictive evidence, not evidence of implementable profitability or authorization to unlock 2026.

## Key evidence

- Market-relative 5-session LightGBM A: mean daily IC `0.0507703` versus absolute A `0.0221228`; positive IC folds `3/3`; positive D10-D1 folds `3/3`.
- Shrunk sector 5-session LightGBM C: natural mean IC `0.0485837`; strict-matched mean IC `0.0444205`.
- 2023 and 2025 remain positive for the selected five-session market-relative result; the result is not a 2024-only effect.
- No fitted model was flagged near-constant.

No trade rules, fees, portfolio logic, backtest, or profitability claim is part of C8.

## Verification

{
  "c8_gpu_suite": "1 passed (C8 XGBoost CUDA)",
  "cpu_suite": "90 passed, 3 skipped (CUDA hidden)"
}
