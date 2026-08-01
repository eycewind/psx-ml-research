# C5 Delivery and Acceptance Report

## Summary and decision

C5 implements deterministic, leakage-safe Ridge regression and Logistic
regression references across the authoritative C4 development folds, with
train-only median imputation/scaling, naive baselines, predeclared fixed-model
evaluation, probability-aware metrics, date-block uncertainty, and coefficient
diagnostics. Same-fold hyperparameter searches are retained only as tuning
diagnostics.

Branch: `feature/c5-baseline-models-and-evaluation`. Contract commit `5326b04`;
implementation `33fc7c3`; diagnostic refinement `ec4012b`; fold-local
selection correction `e5a96f1`; refreshed live reports `472d0a3`; canonical
fixed-model correction `780774e`.

**Result: linear predictive signal was not demonstrated.** Canonical Ridge with
fixed alpha=1 beat the best naive RMSE baseline on 0/3 horizons. Canonical
Logistic regression with fixed C=1 beat the training-prevalence log-loss
baseline on 0/3 horizons. The final 2026 holdout remained locked and was not
accessed.

This is a model-reference result, not a trading result or profitability claim.

## Live evaluation

- Six tasks: gross 5/10/20-session regression and positive-return classification.
- Three C4 validation folds: 2023, 2024, 2025.
- 27 frozen C3 predictors, exact registry order.
- 3,604,040 validation prediction records.
- 972 fold/model/feature coefficient records.
- 742 validation dates and 387 symbols represented.
- Zero convergence warnings.
- CPU only, seed 42, single-thread fitting.

Canonical fixed-alpha Ridge mean R² is negative at every horizon: approximately
-0.519, -0.367, and -0.793 for 5/10/20 sessions. Canonical fixed-C Logistic mean
ROC AUC is approximately 0.488, 0.476, and 0.489. Fold dispersion is substantial
and retained in the model report.

Regression error concentration is material: the top 10 symbols/instruments
account for approximately 42.6%, 41.4%, and 70.6% of canonical Ridge squared loss
at 5/10/20 sessions. C5 records the identifiers but does not infer security type
from names. Classification log loss is much less concentrated (~5.1–5.4% in the
top 10).

## Determinism

Two clean runs from the same source snapshot and configuration produced
byte-identical and logically identical artifacts:

```text
prediction file:    19158674ccaa614496cf8c507603c59848d27b4ef834bc4f09639a6c340ee381
prediction logical: 3bfeea3c20cbe38869eceb3315e5e2babcd98453ecb2daf08391069cbe63fb69
coefficient file:   ed1ea95aa06a8373807bccd6cb81e558dd7f4bf84e0f044878e946d62888a78e
coefficient logical:e82403d0764b6f3d3cbaeeccc926579f0918e1f51303ee06a223fdc0aec218b6
```

## Acceptance mapping

| Contract checks | Evidence |
|---|---|
| 1–6 branch/boundaries | Required branch; C4 research artifacts only; SQLite canary; `tmp_path`; outside/watcher outputs rejected |
| 7–8 feature safety | Config allowlist equals ordered C3 registry; forbidden target/future/identifier prefixes rejected |
| 9–14 preprocessing | Fold/task train-only medians, means, scales; outlier isolation; all-missing and constant handling; order invariance |
| 15–17 fold roles | Only exact C4 train fitted and same-fold validation scored; output contains validation role only |
| 18–19 holdout | Explicit lock raises by default; manifest records `holdout_accessed=false` |
| 20–21 fold/future isolation | Outside-fold target mutation canary and chronological role filtering leave earlier fold predictions unchanged |
| 22–25 baselines/models | Hand baseline, Ridge, deterministic Logistic probability tests |
| 26–28 selection/defaults/warnings | Alpha/C=1 is canonical; same-fold grid scores are labeled biased tuning diagnostics; warnings captured (zero live) |
| 29 shuffled target | Synthetic strong relation loses R² under deterministic target permutation |
| 30–34 metrics | Hand MAE/RMSE/R²/Brier; negative R² retained; probability log loss/Brier/AUC/PR AUC; prevalence reported |
| 35–38 reconciliation/uncertainty/scope labels | Prediction-derived fold metrics; mean/std; deterministic date-block bootstrap; no trading-performance labels |
| 39–41 coefficients | Canonical fixed-model coefficients; exact transformed order, artifact hashes, fold mean/std/sign consistency/near-zero diagnostics |
| 42–44 determinism/config/Git | Matching file/logical hashes; config hash canary; clean Git provenance recorded |
| 45 full suite | Complete CPU-only C1–C5 suite; expected C2 GPU test skip |
| 46–48 scope/watcher | No tree/neural/signal/portfolio/cost/execution/backtest; no profit claim; C14 untouched |

Final CPU-only suite: **51 passed, 1 skipped in 10.52 seconds**. The skip is the
expected C2 GPU availability test; C5 itself is intentionally CPU-only.

## Production safety

Before and after C5:

```text
DB SHA-256: e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b
DB size: 304885760
DB mtime: 1785003631
Watcher HEAD: 404e3637637ca89d4455b9f7069c6191a3658d83
Watcher porcelain status: <empty>
```

## Deviations and judgments

- Scikit-learn is an optional `models` dependency, keeping the C1–C4 core narrow.
- Unweighted Logistic regression only was implemented; balanced Logistic was
  optional and omitted to keep the first falsification matrix compact.
- Ridge uses deterministic Cholesky solving; Logistic uses single-thread L-BFGS.
- Median imputation is used without missing-indicator expansion. Missing and
  constant fields are still recorded by task/fold.
- Fixed alpha=1 and C=1 are the canonical unbiased C5 specifications. All C5
  conclusions, uncertainty, coefficient, and concentration diagnostics use them.
- Same-fold selected hyperparameters minimize the fold they are scored on and
  therefore are optimistically biased tuning diagnostics, not unbiased
  validation metrics. Sequential tuning was not implemented in this correction.
- Date-block intervals cover canonical fixed-model absolute error or log loss;
  same-fold selected intervals remain diagnostic only. IID row bootstrap is not
  used.
- Holdout authorization is recorded, but the development pipeline intentionally
  never emits test predictions even when authorization is supplied. A later
  reviewed contract should define final refit/holdout evaluation.
- No optional rank evaluation, OLS, or Huber model was added.

## Recommendation

C5 is recommended for acceptance as a correct negative linear reference. The
next modeling contract should first address the observed regression outlier/
instrument concentration and universe composition before claiming that model
nonlinearity is the missing ingredient.
