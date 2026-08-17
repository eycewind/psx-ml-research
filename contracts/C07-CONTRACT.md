# C7 — Gradient-Boosted Tree Models and Walk-Forward Evaluation

## Contract identity

- Project: `psx-ml-research`
- Contract: `C7_GRADIENT_BOOSTED_TREE_MODELS_AND_WALK_FORWARD_EVALUATION`
- Required branch: `feature/c7-tree-baseline-models`
- Base: accepted C6 merged into `main`
- Canonical universe: `pit_liquid_ordinary_equity_v1`
- Primary practical model: LightGBM
- Independent verification model: XGBoost, preferably GPU-enabled
- Reference nonlinear model: scikit-learn HistGradientBoosting
- Out of scope: signals, trade rules, position sizing, portfolios, fees, slippage, execution, backtesting, Sharpe, P&L, and profitability claims.

C7 must be implemented and reviewed on its own branch. It must not modify `psx-stock-watcher`, `psx_watcher.db`, or the pending watcher C14 branch.

## Motivation

C5 showed that Ridge and Logistic regression did not demonstrate useful predictive signal. C6 showed that mixed instruments distorted regression error, but the negative linear conclusion remained unchanged after moving to a structurally cleaner ordinary-equity universe.

C7 tests whether nonlinear thresholds and feature interactions provide stable out-of-sample predictive value.

A negative nonlinear result is acceptable if the implementation and evaluation are correct.

## Source boundaries

C7 may read only research-owned artifacts:

```text
data/processed/features/daily_features.parquet
data/processed/targets/daily_feature_targets.parquet
data/processed/datasets/temporal_split_assignments.parquet
data/processed/universe/c6_universe_membership.parquet
artifacts/predictions/c5/validation_predictions.parquet
artifacts/reports/C3_*.json
artifacts/reports/C4_*.json
artifacts/reports/C5_*.json
artifacts/reports/C6_*.json
config/
```

C7 must not:

- connect to SQLite;
- open or modify `psx_watcher.db`;
- modify production watcher code;
- use live external APIs during training or evaluation;
- overwrite C1–C6 outputs;
- use non-equity rows in the canonical C7 universe;
- use the final 2026 holdout during model selection;
- use future or target columns as predictors.

## Canonical universe

Canonical C7 rows must satisfy:

```text
universe_name = pit_liquid_ordinary_equity_v1
point_in_time_eligible = true
valid selected target
valid C4 fold assignment
```

All-instrument and equity-like universes may be reported only as secondary diagnostics. They must not be used to select the final C7 model.

The historical-backcast limitation of the 2026-08-01 PSX security master remains explicit.

## Tasks

### Regression targets

```text
fwd_open_to_close_ret_5s_adj
fwd_open_to_close_ret_10s_adj
fwd_open_to_close_ret_20s_adj
```

### Classification targets

```text
up_5s
up_10s
up_20s
```

### Optional direct ranking

A direct ranking objective may be added only if same-date groups are implemented correctly and the objective remains separate from regression/classification.

Optional labels:

```text
fwd_ret_5s_rank
fwd_ret_20s_rank
```

## Model stack

### Reference nonlinear model

Required:

```text
HistGradientBoostingRegressor
HistGradientBoostingClassifier
```

Purpose:

- minimal-dependency nonlinear reference;
- deterministic CPU benchmark;
- sanity check against library-specific behavior.

### Primary practical model

Required:

```text
LightGBMRegressor
LightGBMClassifier
```

LightGBM is the primary C7 model.

Requirements:

- CPU training as canonical reproducible mode;
- optional GPU mode as a separate named variant;
- early stopping;
- explicit random seed;
- deterministic settings where supported;
- fold-safe validation.

### Independent verification model

Required unless blocked by documented environment incompatibility:

```text
XGBRegressor
XGBClassifier
```

Preferred:

```text
tree_method = hist
device = cuda
```

If GPU is unavailable, CPU XGBoost is acceptable with a documented reason.

XGBoost is an independent implementation check, not just another LightGBM hyperparameter variant.

### Excluded models

C7 must not introduce:

```text
random forest as the primary model
ExtraTrees as the primary model
CatBoost without separate justification
neural networks
transformers
symbol embeddings
reinforcement learning
```

## Feature policy

The canonical predictor list must be the frozen 27-feature C3 registry order unless C7 defines and versions an additional feature set.

Forbidden predictors:

```text
target columns
future returns
classification labels
target ranks
entry/exit/target-end dates
split roles
symbol
trade_date
instrument family
future universe membership
C5/C6 predictions
final-holdout-derived fields
```

Identifiers may remain in prediction artifacts, but never in the model matrix.

C7 v1 must not use symbol identity as a categorical predictor.

## Missing values and preprocessing

Canonical policy:

```text
HistGradientBoosting: native missing-value handling
LightGBM: native missing-value handling
XGBoost: native missing-value handling
```

No global imputation is allowed.

If preprocessing becomes necessary:

- fit on training rows only;
- preserve fold isolation;
- record parameters;
- apply unchanged to validation rows.

Scaling is not required for tree models.

## Fold and holdout policy

C4 assignments are authoritative.

For each fold:

- fit only `train`;
- score only same-fold `validation`;
- exclude `purged`, `embargoed`, `test`, and `not_in_fold`;
- preserve date-level roles.

The final 2026 holdout remains locked by default.

Any attempt to access it must fail unless explicitly authorized:

```text
--allow-final-holdout
```

C7 development must not use this flag.

The manifest must record:

```text
holdout_accessed = false
```

## Hyperparameter strategy

Avoid uncontrolled searches. Use small fixed candidate sets and early stopping.

### HistGradientBoosting candidates

```text
learning_rate = [0.03, 0.05, 0.1]
max_leaf_nodes = [15, 31, 63]
max_depth = [None, 4, 8]
min_samples_leaf = [20, 50, 100]
l2_regularization = [0.0, 1.0, 10.0]
```

Do not evaluate the full Cartesian product unless computationally justified.

### LightGBM candidates

```text
learning_rate = [0.01, 0.03, 0.05]
num_leaves = [15, 31, 63]
max_depth = [-1, 4, 8]
min_data_in_leaf = [20, 50, 100, 250]
feature_fraction = [0.7, 0.9, 1.0]
bagging_fraction = [0.7, 0.9, 1.0]
lambda_l1 = [0.0, 0.1, 1.0]
lambda_l2 = [0.0, 1.0, 10.0]
max_bin = explicit
n_estimators = large cap with early stopping
```

Use a compact manually defined candidate set or deterministic limited search.

### XGBoost candidates

```text
learning_rate = [0.01, 0.03, 0.05]
max_depth = [3, 5, 7]
min_child_weight = [1, 5, 20]
subsample = [0.7, 0.9, 1.0]
colsample_bytree = [0.7, 0.9, 1.0]
reg_alpha = [0.0, 0.1, 1.0]
reg_lambda = [1.0, 10.0]
max_bin = explicit
n_estimators = large cap with early stopping
```

## Leakage-safe selection

The same validation fold may not be used both to select hyperparameters and to claim unbiased performance.

Allowed approaches:

### Sequential walk-forward selection

```text
fold_2023:
    fixed default or train-internal tuning only

fold_2024:
    choose from fold_2023 evidence
    evaluate once on fold_2024

fold_2025:
    choose from folds 2023–2024
    evaluate once on fold_2025
```

### Nested chronological tuning

Use an inner chronological split fully inside the outer training period.

Per-fold oracle selection on the current validation fold is prohibited as the canonical result.

## Early stopping

Early stopping must use only data allowed by the chosen tuning design.

Rules:

- early-stopping data cannot later be claimed as unbiased evaluation;
- no final-holdout data;
- boosting round must be recorded;
- maximum rounds must be explicit;
- no hidden reuse of the current evaluation fold.

## Baselines

### Regression

```text
zero_return_baseline
training_mean_baseline
C5 ridge_fixed_alpha_1
```

### Classification

```text
majority_class_baseline
training_prevalence_baseline
C5 logistic_fixed_c_1
```

A model is not successful merely because it beats Ridge or Logistic if it still fails naive baselines.

## Evaluation metrics

### Regression

Required per fold and aggregate:

```text
MAE
median absolute error
RMSE
R²
Pearson correlation
Spearman correlation
daily Spearman IC
daily IC standard deviation
daily IC positive-date fraction
directional accuracy
Huber loss diagnostic
top/bottom prediction-quantile target spread
```

Quantile spread is predictive analysis, not a portfolio return.

### Classification

Required:

```text
log loss
Brier score
ROC AUC
PR AUC
balanced accuracy
precision
recall
F1
confusion matrix
calibration bins
class prevalence
```

### Stability

Required stratification:

```text
fold
validation year
liquidity bucket
stale-history bucket
sector where available
prediction quantile
```

All subgroup metrics must report row/date/symbol counts.

### Uncertainty

Required:

- fold dispersion;
- deterministic date-block bootstrap intervals;
- date and symbol counts.

IID row bootstrap cannot be the sole uncertainty method.

## Practical-use decision criteria

A model may be called promising only if it demonstrates most of the following.

### Regression/ranking

- positive mean Spearman correlation;
- positive mean daily IC;
- positive IC in at least two of three folds;
- improvement over Ridge and naive baselines;
- stable top-versus-bottom separation;
- no domination by a few symbols or dates;
- acceptable fold dispersion.

### Classification

- ROC AUC meaningfully above 0.50;
- log loss better than training prevalence;
- Brier score better than prevalence;
- stable results in at least two folds;
- acceptable calibration.

No single metric is sufficient.

A model must not be called practical if gains are tiny, unstable, or isolated to one fold.

## Feature importance and explainability

Required for LightGBM and XGBoost:

```text
gain importance
split/count importance
permutation importance on validation data
fold-to-fold importance stability
```

Optional:

```text
SHAP summary diagnostics
```

SHAP must use a deterministic sample and must not become a required heavyweight dependency unless justified.

Feature importance is associational, not causal.

## Sanity and concentration checks

Required diagnostics:

```text
prediction distributions
probability distributions
quantile counts
symbol-level loss concentration
date-level loss concentration
largest residuals
largest-confidence errors
```

Required tests:

1. shuffled targets destroy performance;
2. noise features do not create stable importance;
3. target/future columns are rejected;
4. predictions are not constant;
5. probabilities remain in `[0,1]`;
6. current validation targets are not used for tuning or early stopping;
7. post-boundary rows do not alter earlier predictions.

## GPU policy

### Canonical mode

At least one full C7 run must be reproducible on CPU:

```text
HistGradientBoosting CPU
LightGBM CPU
```

### GPU verification

XGBoost GPU should run on the RTX 5070 where supported.

Record:

```text
GPU model
driver
CUDA runtime
XGBoost version
tree method
device
training time
prediction time
peak memory if available
```

CPU and GPU runs must be separate named variants.

If GPU execution is not bitwise deterministic:

- define tolerances;
- retain CPU reference results;
- report nondeterminism honestly.

## Runtime reporting

For each task/model/fold, record:

```text
fit time
prediction time
boosting rounds
early-stopping round
rows
features
device
thread count
```

Runtime must not be the sole model-selection criterion.

## Outputs

Suggested runtime outputs:

```text
artifacts/models/c7/<task>/<model>/<fold_id>/
artifacts/predictions/c7/<task>/<model>/<fold_id>.parquet
data/processed/model_inputs/c7/
data/processed/diagnostics/c7/
```

Required tracked reports:

```text
artifacts/reports/C7_MODEL_REPORT.md
artifacts/reports/C7_FEATURE_IMPORTANCE_REPORT.md
artifacts/reports/C7_RUNTIME_REPORT.md
contracts/C07-DELIVERY.md
artifacts/reports/C7_MODEL_MANIFEST.json
```

Prediction artifacts must contain:

```text
trade_date
symbol
fold_id
split_role
universe_name
target_name
target
prediction
prediction_probability
model_name
model_version
device
```

No signal or trade-action column may be introduced.

## Manifest requirements

Record:

```text
manifest version
generation timestamp
Git commit and dirty state
C2 environment manifest hash
C3 feature manifest hash
C4 target/split manifest hash
C6 universe manifest hash
input hashes
canonical universe
ordered feature list
target definitions
model/library versions
device details
candidate configurations
selection strategy
selected parameters
early-stopping policy
selected rounds
seed/determinism settings
thread counts
fold IDs/date ranges
holdout access flag
row/date/symbol counts
per-fold metrics
aggregate metrics
baseline metrics
feature-importance hashes
prediction hashes
model hashes
logical hashes
runtime statistics
```

Generation timestamps must not affect logical hashes.

## Suggested architecture

```text
src/psx_ml/tree_models/
├── config.py
├── registry.py
├── datasets.py
├── hist_gradient_boosting.py
├── lightgbm_models.py
├── xgboost_models.py
├── tuning.py
├── early_stopping.py
├── train.py
├── predict.py
├── metrics.py
├── importance.py
├── runtime.py
├── validation.py
├── manifest.py
└── pipeline.py
```

Suggested tests:

```text
tests/tree_models/
├── test_config_boundaries.py
├── test_universe_filter.py
├── test_feature_allowlist.py
├── test_fold_isolation.py
├── test_holdout_lock.py
├── test_hist_gradient_boosting.py
├── test_lightgbm.py
├── test_xgboost.py
├── test_early_stopping.py
├── test_tuning_leakage.py
├── test_metrics.py
├── test_importance.py
├── test_gpu_cpu_consistency.py
├── test_determinism.py
└── test_pipeline.py
```

## Acceptance tests

### Repository and source safety

1. C7 runs only on `feature/c7-tree-baseline-models`.
2. Runtime reads only research-owned artifacts.
3. Runtime makes zero SQLite connections.
4. Source DB and watcher fingerprints remain unchanged.
5. C1–C6 outputs are never overwritten.
6. Tests use temporary paths.
7. Outputs outside the repository are rejected.

### Universe and features

8. Canonical rows belong to `pit_liquid_ordinary_equity_v1`.
9. Non-equity rows cannot enter canonical training/evaluation.
10. Predictors exactly match the C3 allowlist.
11. Targets, identifiers, split fields, future dates, universe fields, and prior predictions are rejected.
12. Symbol identity is not used as a feature.
13. Future rows cannot alter earlier model inputs.

### Fold and holdout safety

14. Only C4 train rows are fitted.
15. Only same-fold validation rows are scored.
16. Purged, embargoed, test, and not-in-fold rows are excluded.
17. Final holdout access fails by default.
18. Manifest records `holdout_accessed=false`.
19. Holdout changes cannot alter development outputs.
20. Another fold’s targets cannot alter the current fold model.
21. Tuning does not improperly use the current evaluation fold.

### Models

22. HistGradientBoosting passes deterministic synthetic tests.
23. LightGBM trains and predicts within tolerance.
24. XGBoost CPU trains and predicts within tolerance.
25. XGBoost GPU runs on the RTX 5070 where supported, or a documented block is recorded.
26. Regression predictions are finite.
27. Classification probabilities lie in `[0,1]`.
28. Early stopping uses permitted data only.
29. Selected rounds are recorded.
30. Candidate sets are fixed and versioned.
31. Shuffled targets destroy performance.
32. Noise features do not create stable importance.

### Metrics and baselines

33. C5 fixed baseline metrics reproduce on the C7 universe.
34. Regression metrics match hand calculations.
35. Classification metrics match hand calculations.
36. Daily IC uses same-date rows only.
37. Minimum daily population is enforced.
38. Quantile ties are deterministic.
39. Fold metrics reconcile with prediction artifacts.
40. Aggregate metrics retain fold dispersion.
41. Date-block uncertainty is deterministic.
42. No metric is labelled profit, Sharpe, or trading performance.

### Importance and diagnostics

43. LightGBM gain/split importance reconciles with fitted models.
44. XGBoost importance reconciles with fitted models.
45. Permutation importance uses validation data without refitting.
46. Feature order is preserved.
47. Importance stability is correct.
48. Loss concentration reconciles to row-level predictions.
49. Prediction distributions and quantiles reconcile.

### Determinism and provenance

50. Repeated CPU runs produce identical logical hashes.
51. GPU runs reproduce within documented tolerance.
52. Value-changing config changes relevant hashes.
53. Library versions and device details are recorded.
54. Git commit and dirty state are recorded.
55. Runtime statistics are recorded.
56. Full C1–C7 suite passes with CUDA hidden.
57. GPU-specific tests pass with CUDA enabled where supported.

### Scope

58. No signal generation is introduced.
59. No fees, brokerage, spread, slippage, or execution logic is introduced.
60. No portfolio or backtest is introduced.
61. No profitability claim is made.
62. Pending watcher C14 remains untouched.

## Required implementation sequence

1. Confirm C6 is merged and tagged.
2. Create `feature/c7-tree-baseline-models` from updated `main`.
3. Confirm canonical universe counts and C5 baseline reproduction.
4. Add dependencies only in the dedicated environment.
5. Implement HistGradientBoosting.
6. Implement LightGBM CPU.
7. Implement XGBoost CPU and GPU.
8. Implement leakage-safe tuning.
9. Implement leakage-safe early stopping.
10. Implement fold-safe predictions.
11. Implement metrics and uncertainty.
12. Implement importance and concentration diagnostics.
13. Run canonical CPU evaluation.
14. Run GPU verification.
15. Compare against naive and C5 fixed baselines.
16. Generate reports and manifest.
17. Run complete CPU-only C1–C7 suite.
18. Run GPU-specific tests.
19. Produce delivery evidence.
20. Do not merge before acceptance.

## Acceptance decision

C7 may be accepted even if boosted-tree models fail.

A positive result requires:

- stable improvement over naive and C5 linear baselines;
- positive and reasonably consistent ranking metrics;
- no one-fold-only effect;
- no domination by a few symbols or dates;
- reproducible CPU results;
- independently verified XGBoost behavior;
- final holdout remaining locked.

A negative result must be reported honestly.

C7 is a predictive-model evaluation contract, not a trading-strategy contract. Practical trading value can only be assessed later in a fee-aware signal and execution contract.
