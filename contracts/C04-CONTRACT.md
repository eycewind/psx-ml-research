# C4 — Leakage-Safe Targets and Temporal Dataset Splits

## 1. Contract identity

- **Project:** `psx-ml-research`
- **Contract:** `C4_LEAKAGE_SAFE_TARGETS_AND_TEMPORAL_SPLITS`
- **Required branch:** `feature/c4-targets-and-temporal-splits`
- **Base:** accepted C3 merged into `main`
- **Purpose:** create reproducible forward-looking labels and leakage-safe train/validation/test split assignments from the accepted C3 feature panel.
- **Out of scope:** model fitting, hyperparameter tuning, predictions, signals, portfolio construction, transaction costs, execution simulation, backtesting, and profitability claims.

C4 must be implemented and reviewed on its own feature branch. It must not modify `psx-stock-watcher`, its database, or the pending watcher C14 branch.

## 2. Inputs and boundaries

C4 may read only research-owned artifacts inside `psx-ml-research`:

- C3 feature Parquet and manifest;
- C1 daily OHLCV Parquet when target price fields are required;
- C1 extraction manifest;
- point-in-time eligibility carried by C3 or the C1 PIT universe artifact.

C4 must not connect to SQLite, open `psx_watcher.db`, query production tables, copy source databases, or infer undocumented field meanings.

Runtime outputs belong under ignored paths such as:

```text
data/processed/targets/
data/processed/datasets/
```

Small manifests, schemas, contracts, and acceptance reports remain tracked.

## 3. Timing policy

### 3.1 Feature availability

A feature row labelled trade date `D`:

- may use observations through close `D`;
- is available only after close `D`;
- cannot support a decision or execution on `D`;
- may support a decision no earlier than the next PSX trading session.

### 3.2 Canonical entry

For `(symbol, D)`:

```text
decision_time = after close D
entry_date    = next exchange trade date after D
entry_price   = adjusted open on entry_date
```

If the symbol has no valid adjusted open on that exact next exchange date, the canonical target is null. C4 must not jump forward several days and call that the next-session entry.

### 3.3 Canonical exits

Initial horizons:

```text
1, 5, 10, 20 exchange sessions after entry
```

For horizon `H`:

```text
exit_date    = H-th exchange session after entry_date
exit_price   = adjusted close on exit_date
gross_return = exit_price / entry_price - 1
```

If the symbol has no valid observation on the required exit date, the target is null. No later observation may be substituted.

### 3.4 Optional analytical targets

Clearly named close-to-close analytical targets may be added, but they must be labelled non-executable from the after-close `D` information set.

### 3.5 Target availability

Every target row must record:

- feature trade date;
- entry date;
- target end date;
- horizon;
- validity or null reason.

A target is known only after `target_end_date`.

## 4. Canonical target set

### 4.1 Regression

Required gross-return targets:

```text
fwd_open_to_close_ret_1s_adj
fwd_open_to_close_ret_5s_adj
fwd_open_to_close_ret_10s_adj
fwd_open_to_close_ret_20s_adj
```

### 4.2 Classification

Required labels derived directly from regression targets:

```text
up_5s
up_10s
up_20s
```

Definition:

```text
1 if gross_return > 0
0 if gross_return <= 0
null if gross_return is null
```

No cost-adjusted label may be introduced without an explicit transaction-cost contract. Gross labels must not be described as profitable trades.

### 4.3 Cross-sectional labels

Optional same-date PIT-safe ranks:

```text
fwd_ret_5s_rank
fwd_ret_20s_rank
```

Rules:

- only point-in-time eligible rows on feature date `D`;
- only valid targets;
- deterministic average ties;
- configured minimum population;
- null on ineligible rows;
- no retrospective use of today's universe.

## 5. Missing-data and PSX rules

C4 must preserve C1/C3 semantics:

- missing symbol-date rows are not zero-volume candles;
- open or close outside high/low is not by itself invalid;
- `high < low` remains a strict source-quality issue;
- null or nonpositive entry/exit prices produce null targets;
- absent next-session observations are never forward-filled;
- suspended, inactive, or delisted histories remain represented through explicit null reasons.

Suggested null reasons:

```text
missing_next_session_observation
missing_entry_open
nonpositive_entry_open
missing_exit_observation
missing_exit_close
nonpositive_exit_close
insufficient_future_sessions
```

## 6. Outputs

### 6.1 Full labelled panel

```text
data/processed/targets/daily_feature_targets.parquet
```

Must retain:

- unique `(trade_date, symbol)`;
- all C3 feature columns;
- `point_in_time_eligible`;
- targets;
- entry/exit dates or normalized equivalent;
- validity/null-reason metadata.

### 6.2 Eligible primary-target panel

Optional filtered output:

```text
data/processed/datasets/eligible_primary_target.parquet
```

Filtering must be explicit in configuration and manifest. The full labelled panel remains canonical.

## 7. Temporal splitting

Random row-level splitting is prohibited.

### 7.1 Split unit

All symbols on the same feature date must receive the same split role for a fold.

### 7.2 Walk-forward design

Use deterministic chronological assignments:

- expanding training window;
- following validation window;
- optional final untouched test window;
- multiple folds where coverage allows.

Exact boundaries must be configuration-driven and manifested.

### 7.3 Purging

For every fold:

```text
maximum training target_end_date < validation feature start date
```

Rows whose target interval overlaps validation or test must be purged using actual `target_end_date`, not a guessed calendar offset.

### 7.4 Embargo

An optional embargo may follow validation windows. It supplements but does not replace purging.

### 7.5 Final holdout

The final test period must remain untouched by later model selection.

### 7.6 Split assignment output

Suggested schema:

```text
trade_date
symbol
fold_id
split_role
included
exclusion_reason
```

Suggested roles:

```text
train
validation
test
purged
embargoed
not_in_fold
```

## 8. Configuration and versioning

Suggested files:

```text
config/targets.yaml
config/splits.yaml
```

Configuration must include target-set version, price family, entry/exit conventions, horizons, classification definitions, PIT rank policy, primary target, fold boundaries, purging, embargo, and output paths.

Any value-changing modification requires a new target-set or split-set version.

## 9. Provenance manifest

Required fields:

```text
manifest version
target-set name/version
split-set name/version
generation timestamp
Git commit and dirty state
C3 feature and manifest hashes
C1 price-source hashes if used
row/symbol/date counts
PIT-eligible count
target definitions
entry/exit conventions
horizons
valid/null counts by target
null-reason counts
classification definitions
cross-sectional method
fold definitions
purge/embargo policy
per-fold counts
output and logical hashes
configuration hashes
```

Generation timestamps must be excluded from logical-content hashes.

## 10. Reports

Required:

```text
artifacts/reports/C4_TARGET_REPORT.md
artifacts/reports/C4_SPLIT_REPORT.md
contracts/C04-DELIVERY.md
artifacts/reports/C4_TARGET_SPLIT_MANIFEST.json
```

The target report must include coverage, null reasons, return percentiles, class balance, PIT rank populations, hand-reconciled examples, and a warning that targets are gross.

The split report must include exact fold boundaries, train/validation/test counts, purged/embargoed counts, overlap verification, date/symbol coverage, and final holdout boundaries.

## 11. Suggested architecture

```text
src/psx_ml/
├── targets/
│   ├── config.py
│   ├── calendar.py
│   ├── forward_returns.py
│   ├── labels.py
│   ├── registry.py
│   ├── validation.py
│   ├── manifest.py
│   └── pipeline.py
├── splits/
│   ├── config.py
│   ├── walk_forward.py
│   ├── purge.py
│   ├── validation.py
│   ├── manifest.py
│   └── pipeline.py
└── reporting/
    ├── target_report.py
    └── split_report.py
```

GPU use is unnecessary.

## 12. Acceptance tests

### Source and boundaries

1. Reads only research-owned Parquet/JSON/config inputs.
2. Runtime modules make zero SQLite connections.
3. Source DB and watcher fingerprints remain unchanged.
4. Tests use temporary outputs.
5. Outputs outside the research repository are rejected.

### Target correctness

6. Feature date `D` maps to the next exchange session as entry.
7. Entry never uses open or close from `D`.
8. Missing symbol observation on that next exchange date yields null.
9. Each horizon maps to the exact exchange exit date.
10. Missing required exit observation yields null.
11. Hand-calculated returns match.
12. Invalid entry/exit prices produce deterministic null reasons.
13. Appending rows after target end does not alter earlier targets.
14. Another symbol's future history cannot alter a target.
15. Open/close outside high-low does not invalidate a valid target.
16. Regression and classification labels reconcile exactly.
17. PIT cross-sectional labels use only same-date eligible valid rows.
18. Cross-sectional ties are deterministic.
19. Ineligible rows have null cross-sectional ranks.
20. No infinities remain.

### Split safety

21. All symbols on the same date share the same split role.
22. Membership is chronological and deterministic.
23. No random row-level splitting exists.
24. Every included training row satisfies `target_end_date < validation_start_date`.
25. Violations are marked purged.
26. Embargo matches configuration.
27. Final test dates never appear in training or validation.
28. Fold boundaries are invariant to input order.
29. Appending data after the configured final boundary does not alter earlier assignments.
30. Per-fold manifest counts reconcile.

### Determinism and provenance

31. Repeated target generation gives identical logical hashes.
32. Repeated split generation gives identical logical hashes.
33. Manifest counts and hashes reconcile.
34. Target registry equals output target schema.
35. Value-changing config changes relevant hashes.
36. Git commit and dirty state are recorded.
37. Full C1-C4 suite passes with CUDA hidden.

### Scope

38. No model fitting, predictions, signals, portfolio logic, costs, execution, or backtest.
39. Gross targets are not described as profitability.
40. Watcher C14 remains untouched.

## 13. Implementation sequence

1. Merge and tag accepted C3.
2. Create `feature/c4-targets-and-temporal-splits` from updated `main`.
3. Inspect actual C1/C3 schemas and manifests.
4. Finalize target and split configs.
5. Implement exchange-session calendar mapping.
6. Implement targets and null-reason accounting.
7. Implement walk-forward splits with purging.
8. Add synthetic hand-calculation tests first.
9. Add live reconciliation and safety checks.
10. Generate deterministic outputs and reports.
11. Run complete CPU-only C1-C4 tests.
12. Produce C4 delivery evidence.
13. Do not merge before acceptance.

## 14. Acceptance decision

C4 may be accepted only when next-session entry alignment, exact exchange-session exits, explicit null handling, PIT-safe ranks, purged temporal splits, deterministic outputs, manifest reconciliation, and production-source safety are all proven.

C4 establishes trustworthy labels and evaluation partitions. It does not establish predictive value or profitability.
