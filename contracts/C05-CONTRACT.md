# C5 — Linear Baseline Models and Walk-Forward Evaluation

## Contract identity

- Project: `psx-ml-research`
- Contract: `C5_LINEAR_BASELINES_AND_WALK_FORWARD_EVALUATION`
- Required branch: `feature/c5-baseline-models-and-evaluation`
- Base: accepted C4 merged into `main`
- Purpose: establish reproducible, leakage-safe linear regression and classification baselines using C4 targets and temporal folds.
- Out of scope: tree models, neural networks, signals, portfolios, transaction costs, execution simulation, backtesting, and profitability claims.

C5 is a reference and falsification stage. A result showing little or no predictive value is acceptable and must be reported honestly.

## Inputs and boundaries

C5 may read only research-owned C4 outputs and tracked configuration/manifest files. It must not connect to SQLite, open `psx_watcher.db`, modify `psx-stock-watcher`, regenerate C1-C4 silently, or use future/target columns as model features.

Runtime outputs belong under ignored paths such as:

```text
artifacts/models/c5/
artifacts/predictions/c5/
data/processed/model_inputs/c5/
```

Tracked outputs:

```text
artifacts/reports/C5_MODEL_REPORT.md
artifacts/reports/C5_COEFFICIENT_REPORT.md
contracts/C05-DELIVERY.md
artifacts/reports/C5_MODEL_MANIFEST.json
```

## Research questions

C5 must determine whether C3 primitive features provide measurable out-of-sample linear predictive information, whether regularization improves stability, whether results persist across folds and horizons, and whether any apparent result is concentrated in one period or a few symbols.

C5 must not claim that a trading strategy is profitable.

## Tasks and models

### Regression targets

```text
fwd_open_to_close_ret_5s_adj
fwd_open_to_close_ret_10s_adj
fwd_open_to_close_ret_20s_adj
```

Required baselines and model:

```text
zero_return_baseline
training_mean_baseline
ridge_regression
```

Optional diagnostic:

```text
ordinary_least_squares
huber_regression
```

### Classification targets

```text
up_5s
up_10s
up_20s
```

Required baselines and model:

```text
majority_class_baseline
training_prevalence_baseline
logistic_regression
```

Unweighted and `class_weight="balanced"` logistic variants may be evaluated, but must be named separately.

### Optional ranking evaluation

Predictions may be evaluated against `fwd_ret_5s_rank` and `fwd_ret_20s_rank`. This is evaluation only, not portfolio construction.

## Feature policy

The canonical model feature list must come from the C3 registry and be frozen in C5 configuration.

Forbidden predictors:

```text
all forward-return targets
all classification labels
all target ranks
target validity/null reasons
entry/exit/target-end dates
split roles
symbol
trade_date
future universe membership
any non-registered C3 feature
```

`symbol` and `trade_date` may remain identifiers only.

Canonical rows must be point-in-time eligible, have a valid target, and belong to the configured C4 fold role.

## Train-only preprocessing

For every fold:

1. fit imputation on training rows only;
2. fit scaling on training rows only;
3. apply unchanged transformations to validation rows;
4. record missing and constant features;
5. reject any validation/test influence on preprocessing.

Recommended v1:

```text
median imputation fitted on training only
optional missing indicators
StandardScaler fitted on training only
no clipping initially
```

If clipping is later enabled, thresholds must be learned from training only and versioned as a separate model variant.

## Fold and holdout policy

C4 assignments are authoritative.

For each fold:

- fit only rows marked `train`;
- score only same-fold rows marked `validation`;
- exclude `purged`, `embargoed`, `test`, and `not_in_fold`;
- preserve date-level split roles.

The final C4 holdout must be locked by default. Access requires an explicit flag such as:

```text
--allow-final-holdout
```

The manifest must record whether holdout rows were accessed.

## Hyperparameters

Ridge grid:

```text
alpha = [0.01, 0.1, 1.0, 10.0, 100.0]
```

Logistic grid:

```text
C = [0.01, 0.1, 1.0, 10.0]
penalty = L2
max_iter = explicit
solver = deterministic supported solver
```

Selection must use validation folds only. Fixed-default model results must also be retained.

## Baselines

Regression:

```text
predict_zero
predict_training_mean
```

Classification:

```text
predict_training_majority_class
predict_training_prevalence_probability
```

A trained model that does not beat naive baselines consistently must be reported as not demonstrating useful out-of-sample signal.

## Metrics

### Regression

Required per fold and aggregate:

```text
MAE
RMSE
R²
Pearson correlation
Spearman rank correlation
directional accuracy
valid observation count
```

Negative R² must be preserved.

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

Accuracy alone is insufficient.

### Uncertainty

Report fold dispersion and deterministic date-block bootstrap intervals for selected metrics. IID row bootstrap is prohibited as the sole uncertainty method.

## Coefficient diagnostics

Store and report:

```text
intercept
coefficient by feature
standardized coefficient
sign
absolute-magnitude rank
fold mean/std
sign consistency
near-zero count
convergence warnings
```

Coefficients are associational, not causal. Correlated-feature instability must be visible.

## Leakage controls

C5 must prove:

1. preprocessing is training-only;
2. target/future columns cannot enter the matrix;
3. C4 purge and embargo roles are honored;
4. appending later data does not alter earlier fold inputs or predictions;
5. modifying another fold's targets does not alter the current fold model;
6. symbol/date identifiers cannot become predictors;
7. final holdout is inaccessible by default;
8. metrics use only genuinely out-of-sample predictions;
9. shuffled training targets destroy apparent performance within documented tolerance.

## Determinism

Use C2 policy:

```text
seed = 42
deterministic = true where supported
```

For identical inputs/config/environment/Git state, coefficients, predictions, metrics, and logical hashes must match within documented numerical tolerance. Thread counts should be explicit where supported.

GPU use is unnecessary.

## Prediction artifact schema

At minimum:

```text
trade_date
symbol
fold_id
split_role
target_name
target
prediction
prediction_probability
model_name
model_version
```

No trading signal column may be introduced.

## Manifest requirements

Record:

```text
manifest version
generation timestamp
Git commit and dirty state
C2/C3/C4 manifest hashes
input Parquet hashes
ordered feature allowlist
target definitions
model names/versions
hyperparameter grids
selected hyperparameters
preprocessing parameters by fold
seed/determinism policy
fold IDs/date ranges
holdout access flag
row/date/symbol counts
missing/constant/dropped features
per-fold and aggregate metrics
baseline metrics
coefficient hashes
prediction hashes
logical-content hashes
```

Generation timestamps must not affect logical hashes.

## Suggested architecture

```text
src/psx_ml/models/
├── config.py
├── registry.py
├── baselines.py
├── preprocessing.py
├── linear_regression.py
├── linear_classification.py
├── train.py
├── predict.py
├── validation.py
├── metrics.py
├── coefficients.py
├── manifest.py
└── pipeline.py
```

Tests:

```text
tests/models/
├── test_config_boundaries.py
├── test_feature_allowlist.py
├── test_preprocessing_leakage.py
├── test_baselines.py
├── test_linear_regression.py
├── test_logistic_regression.py
├── test_fold_isolation.py
├── test_holdout_lock.py
├── test_metrics.py
├── test_coefficients.py
├── test_determinism.py
└── test_pipeline.py
```

## Acceptance tests

1. C5 runs on the required feature branch.
2. Runtime reads only research-owned artifacts.
3. Runtime makes zero SQLite connections.
4. Production DB/watcher fingerprints remain unchanged.
5. Tests use temporary outputs.
6. Outputs outside the repository are rejected.
7. Ordered model features exactly match the configured C3 allowlist.
8. Target/future/date/symbol/split columns are rejected as predictors.
9. Imputation is fitted only on training rows.
10. Scaling is fitted only on training rows.
11. Validation outliers cannot alter training transforms.
12. All-missing training features are deterministic.
13. Constant training features are deterministic and reported.
14. Input row order does not alter transforms.
15. Only C4 train rows are fitted.
16. Only same-fold validation rows are scored during development.
17. Purged/embargoed/test/not-in-fold rows are excluded.
18. Final holdout access fails by default.
19. Manifest records holdout access.
20. Changing targets outside a fold cannot alter that fold model.
21. Appending post-boundary rows cannot alter earlier predictions.
22. Zero and mean regression baselines are correct.
23. Majority and prevalence classification baselines are correct.
24. Ridge matches a hand-calculated synthetic case.
25. Logistic probabilities match a deterministic synthetic case.
26. Hyperparameter selection uses validation only.
27. Fixed-default metrics are retained.
28. Convergence warnings are captured.
29. Target shuffling removes apparent performance.
30. Regression metrics match hand calculations.
31. Classification metrics match hand calculations.
32. Negative R² is preserved.
33. Probability metrics use probabilities.
34. PR AUC and prevalence are both reported.
35. Fold metrics reconcile with predictions.
36. Aggregate metrics retain fold dispersion.
37. Date-block uncertainty is deterministic.
38. No metric is labelled profit, Sharpe, or trading performance.
39. Coefficients align exactly with transformed feature order.
40. Coefficient artifacts reconcile with fitted models.
41. Sign-consistency calculations are correct.
42. Repeated runs match within tolerance.
43. Value-changing config changes relevant hashes.
44. Git commit and dirty state are recorded.
45. Full C1-C5 suite passes with CUDA hidden.
46. No tree model, neural net, signal, portfolio, costs, execution, or backtest is introduced.
47. No profitability claim is made.
48. Watcher C14 remains untouched.

## Initial model matrix

| Task | Target | Baselines | Model |
|---|---|---|---|
| Regression | 5-session return | zero, training mean | Ridge |
| Regression | 10-session return | zero, training mean | Ridge |
| Regression | 20-session return | zero, training mean | Ridge |
| Classification | 5-session positive return | majority, prevalence | Logistic |
| Classification | 10-session positive return | majority, prevalence | Logistic |
| Classification | 20-session positive return | majority, prevalence | Logistic |

Run unweighted variants first. Add balanced logistic regression only as a separately named variant.

## Required implementation sequence

1. Confirm C4 is merged and tagged.
2. Confirm branch `feature/c5-baseline-models-and-evaluation`.
3. Inspect actual C4 schemas and manifest.
4. Freeze feature allowlist and task matrix.
5. Implement naive baselines.
6. Implement train-only preprocessing.
7. Implement Ridge.
8. Implement logistic regression.
9. Implement fold-safe training/prediction.
10. Implement metrics and coefficient diagnostics.
11. Implement holdout lock.
12. Add synthetic leakage and hand-calculation tests.
13. Run development folds without holdout access.
14. Generate reports and manifest.
15. Run complete CPU-only C1-C5 suite.
16. Produce delivery evidence.
17. Do not merge before review.

## Acceptance decision

C5 may be accepted even if linear models fail to beat naive baselines.

Acceptance depends on correct leakage-safe implementation, exact C4 fold use, train-only preprocessing, locked holdout, valid baseline comparisons, deterministic artifacts, transparent coefficients, and no trading claims.

A negative result is useful because it establishes the reference level later nonlinear models must beat.
