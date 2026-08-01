# C3 — Point-in-Time Feature Engineering

## 1. Contract status

- **Project:** `psx-ml-research`
- **Contract:** `C3_POINT_IN_TIME_FEATURE_ENGINEERING`
- **Required implementation branch:** `feature/c3-point-in-time-features`
- **Base branch:** accepted C2 `main`
- **Merge rule:** implement and validate C3 entirely on its own feature branch. Merge into `main` only after every C3 acceptance test passes and the delivery report has been reviewed and accepted.
- **Source boundary:** `psx-stock-watcher` and `psx_watcher.db` remain read-only and must not be accessed by the C3 feature pipeline. C3 must consume only C1-controlled local research extracts and metadata.
- **C14 boundary:** do not modify, merge, rebase, cherry-pick, or otherwise interact with the pending C14 watcher branch.

## 2. Purpose

C3 creates a deterministic, leakage-safe feature-engineering pipeline for Pakistan Stock Exchange daily data.

The objective is to convert C1’s audited daily OHLCV extract and point-in-time universe into documented feature tables whose values for trade date `D` use only observations available on or before `D`.

C3 is not a model-performance contract. It must not train models, construct trading signals, claim profitability, or run backtests.

C3 must prove that:

1. every feature has a defined formula, input field family, lookback, warm-up rule, null policy, and availability time;
2. feature values are computed independently per symbol unless explicitly documented as cross-sectional or market-wide;
3. rolling features never use future rows;
4. point-in-time universe membership is respected without applying today’s membership retrospectively;
5. feature outputs are deterministic for the same C1 snapshot, configuration, and code version;
6. downstream contracts can reproduce exactly which source rows and feature definitions generated a dataset; and
7. PSX-specific source conventions are preserved rather than incorrectly “cleaned.”

## 3. Timing and leakage convention

### 3.1 Feature timestamp

Each output row is keyed by:

```text
trade_date
symbol
```

A feature row for trade date `D` represents information available **after the close of session `D`**.

Therefore:

- C3 may use the complete OHLCV observation for `D`;
- a row for `D` must never be used to simulate a trade before or during session `D`;
- the earliest permitted downstream decision time is the next trading session after `D`;
- target construction and execution timing belong to a later contract and must preserve this convention.

The feature table must include or document an availability semantic equivalent to:

```text
feature_asof_date = trade_date
available_after = market close on trade_date
```

### 3.2 Trailing-only rule

For each symbol and date `D`, a rolling feature may use only rows satisfying:

```text
row.trade_date <= D
```

No centered windows, backward fills from future observations, whole-series normalization, or future-aware interpolation are permitted.

### 3.3 Cross-sectional rule

A cross-sectional feature for date `D` may use only rows for date `D` that are eligible under the point-in-time universe definition for `D`, unless the feature explicitly represents the entire observed market and is named/documented accordingly.

Cross-sectional ranks, percentiles, medians, means, and dispersion statistics must be recomputed independently for each date.

## 4. Inputs

C3 must consume C1-controlled research artifacts, not production SQLite.

Required logical inputs:

```text
data/cache/daily_ohlcv.parquet
data/cache/point_in_time_universe.parquet
C1 extraction manifest
C1 schema/audit metadata
```

Equivalent configured paths are acceptable.

The input manifest must be validated before feature generation. At minimum, C3 must verify:

- manifest version is supported;
- source row count agrees with the daily Parquet file;
- symbol count and date range reconcile;
- required canonical fields exist;
- input files match recorded hashes if C1 records them;
- point-in-time universe keys are unique;
- daily OHLCV keys are unique;
- input rows are ordered or explicitly sorted deterministically by `symbol, trade_date` before rolling operations.

If validation fails, feature generation must stop with a clear error. It must not silently repair the C1 dataset.

## 5. PSX-specific source rules

### 5.1 Open and close outside high/low

PSX source data may legitimately contain `open` or `close` values outside the reported `low..high` interval because of source and auction conventions already documented in C1.

Therefore C3 must:

- preserve those rows;
- not mark them invalid solely for that reason;
- not clip open or close into the high/low interval;
- not discard them from feature computation solely for that reason;
- optionally carry C1 audit flags as metadata or diagnostic features, but not reinterpret them as impossible prices.

A strict impossible-range condition remains:

```text
high < low
```

Rows rejected or masked for other reasons must be reported explicitly.

### 5.2 Missing observations are not zero-volume observations

C1 established that the upstream source can omit observations rather than store zero-volume rows.

C3 must distinguish:

- a stored row whose volume is zero;
- a stored row whose volume is null;
- an absent symbol/date observation;
- a symbol not yet listed or no longer observed;
- a date on which the exchange itself has no session.

C3 must not synthesize a zero-volume OHLCV row for an absent observation.

### 5.3 Raw versus adjusted fields

C3 must implement an explicit field-selection policy. It must never mix raw and adjusted values inside one formula without documentation.

At minimum, the policy must identify:

- price family used for returns and momentum;
- price family used for range and volatility features;
- volume family used for liquidity features;
- how adjustment-factor quarantine or warnings from C1 are surfaced.

Recommended initial policy:

```text
return/momentum features: adjusted close where C1 marks it usable
range features: one internally consistent OHLC family
liquidity features: volume paired with the same adjustment family as price
raw fields: retained for audit/reference features
```

Because C1 noted that algebraic adjustment integrity does not by itself prove correct dividend treatment, C3 must record the limitation in its feature report and manifest. C3 must not claim total-return correctness unless independently established.

A configuration option may generate separate raw and adjusted feature sets. If implemented, names must make the field family unambiguous and tests must prevent accidental mixing.

## 6. Scope

### 6.1 In scope

C3 must define and implement:

- feature configuration;
- feature registry and metadata;
- point-in-time-safe per-symbol rolling calculations;
- point-in-time-safe cross-sectional calculations;
- warm-up and null handling;
- stale/missing-observation-aware calculations;
- deterministic feature output;
- feature quality and coverage reporting;
- feature provenance manifest;
- versioned local Parquet output;
- unit, property, and integration tests;
- a Markdown feature report;
- a C3 delivery and acceptance report.

### 6.2 Explicitly out of scope

C3 must not implement:

- prediction targets or labels;
- future returns;
- train/validation/test splits;
- model classes;
- model fitting;
- hyperparameter optimization;
- feature selection based on target performance;
- predictions or probability scores;
- buy/sell signals;
- portfolio construction;
- transaction costs;
- execution simulation;
- backtesting;
- profitability or Sharpe-ratio claims;
- fundamental-data features unless a later contract adds an audited point-in-time source;
- news, sentiment, social-media, insider, corporate-action, or macroeconomic features;
- writes to or direct runtime reads from `psx_watcher.db`.

## 7. Required repository changes

The implementation should add or update a structure similar to:

```text
psx-ml-research/
├── config/
│   └── features.example.toml
├── contracts/
│   └── C3_POINT_IN_TIME_FEATURE_ENGINEERING/
│       └── CONTRACT.md
├── src/
│   └── psx_ml/
│       └── features/
│           ├── __init__.py
│           ├── config.py
│           ├── registry.py
│           ├── base.py
│           ├── price.py
│           ├── volume.py
│           ├── volatility.py
│           ├── liquidity.py
│           ├── cross_sectional.py
│           ├── quality.py
│           ├── pipeline.py
│           └── manifest.py
├── tests/
│   ├── features/
│   │   ├── test_price_features.py
│   │   ├── test_volume_features.py
│   │   ├── test_volatility_features.py
│   │   ├── test_liquidity_features.py
│   │   ├── test_cross_sectional_features.py
│   │   ├── test_point_in_time_safety.py
│   │   ├── test_missing_history.py
│   │   ├── test_determinism.py
│   │   └── test_source_safety.py
│   └── test_feature_pipeline.py
├── data/
│   └── processed/
│       └── features/
├── artifacts/
│   └── reports/
│       ├── C3_FEATURE_REPORT.md
│       └── C3_DELIVERY.md
└── notebooks/
```

Equivalent names are acceptable if responsibilities remain separated.

Generated feature Parquet files, temporary data, caches, and bulky profiling artifacts must remain ignored by Git. Small contracts, schema definitions, manifests, feature catalogs, and Markdown reports should remain version-controlled.

## 8. Configuration

Provide a configuration similar to:

```toml
[input]
daily_path = "data/cache/daily_ohlcv.parquet"
universe_path = "data/cache/point_in_time_universe.parquet"
manifest_path = "data/cache/MANIFEST.json"

[output]
feature_path = "data/processed/features/daily_features.parquet"
manifest_path = "data/processed/features/FEATURE_MANIFEST.json"
report_path = "artifacts/reports/C3_FEATURE_REPORT.md"

[fields]
price_family = "adjusted"       # adjusted | raw
volume_family = "adjusted"      # adjusted | raw

[windows]
short = [1, 2, 5]
medium = [10, 20]
long = [40, 60, 120]

[quality]
minimum_history = 20
stale_run_threshold = 5
minimum_cross_section_size = 20

[execution]
engine = "cpu"
float_precision = "float64"
```

C3 should remain CPU-first. The RTX 5070 runtime established in C2 may be retained for later modeling, but daily PSX feature engineering is not expected to benefit enough from GPU acceleration to justify a GPU-specific implementation in C3.

Configuration must be validated strictly. Unknown field families, nonpositive windows, duplicate windows, contradictory output paths, or missing required inputs must fail clearly.

## 9. Feature registry and metadata

Every feature must be registered with metadata equivalent to:

```text
name
version
description
category
formula
input columns
raw/adjusted field family
lookback observations
minimum observations
symbol-level or cross-sectional
availability convention
null policy
missing-observation policy
stale-price sensitivity
output dtype
```

Feature names must be stable, machine-safe, and unambiguous. Examples:

```text
ret_1d_adj
log_ret_5d_adj
close_to_open_1d_adj
rv_20d_adj
turnover_median_20d_adj
volume_ratio_20d_adj
amihud_20d_adj
ret_rank_20d_adj
```

Do not use vague names such as `momentum`, `volatility`, or `volume_avg` without the window and field family.

Feature-definition changes that alter values must increment either:

- feature version;
- manifest schema version; or
- code version captured in provenance.

## 10. Initial feature families

The initial C3 feature set should be deliberately compact. It should prefer transparent primitives over a large collection of overlapping technical indicators.

### 10.1 Price return and momentum features

Candidate features:

```text
simple returns over 1, 2, 5, 10, 20, 40, 60 observations
log returns over 1, 5, 10, 20, 60 observations
close/open return for the current session
open/previous-close gap return
rolling cumulative return over selected windows
price relative to trailing rolling maximum
price relative to trailing rolling minimum
price relative to trailing mean
```

Rules:

- a `k`-observation return compares the current stored observation with the stored observation `k` rows earlier for the same symbol;
- it must not assume that `k` observations equal `k` calendar days;
- gap-sensitive features must explicitly identify when the previous stored observation is separated by missing exchange sessions;
- division by zero or nonpositive prices must produce null plus a quality flag, not infinity.

### 10.2 Volume and turnover features

Candidate features:

```text
log1p volume
rolling mean/median volume over 5, 20, 60 observations
current volume divided by trailing median volume
volume coefficient of variation
price × volume turnover
rolling median turnover
turnover percentile/rank by date
missing-volume flag
zero-volume flag
```

Rules:

- median-based baselines should be preferred where extreme volumes are common;
- absent symbol/date rows must not be converted into zero volume;
- adjusted price must be paired with adjusted volume when producing adjustment-consistent turnover, unless the feature is explicitly raw.

### 10.3 Volatility and range features

Candidate features:

```text
rolling standard deviation of log returns over 5, 10, 20, 60 observations
rolling mean absolute return
high-low range divided by a documented price denominator
true range using current high/low and previous close
rolling average true range as a primitive feature
rolling downside and upside semideviation
```

Rules:

- formulas must remain valid under the PSX convention where open or close can lie outside reported high/low;
- C3 must not use a formula whose assumptions are knowingly violated without documenting and testing the consequence;
- avoid silently importing indicator-library defaults.

### 10.4 Liquidity and tradability features

Candidate features:

```text
rolling median turnover
rolling fraction of observed exchange sessions
days since previous observation
rolling missing-observation rate
Amihud-style absolute return / turnover measure
stale-close run length
fraction of unchanged closes in a trailing window
point-in-time universe eligibility flag
```

Rules:

- liquidity must use only trailing information;
- no future universe membership may affect past dates;
- denominators at or near zero must be handled explicitly;
- stale-price features are descriptive and must not automatically imply data corruption.

### 10.5 Cross-sectional features

Candidate features computed independently for each trade date:

```text
return percentile/rank
momentum percentile/rank
volatility percentile/rank
turnover percentile/rank
liquidity percentile/rank
market-median-relative return
cross-sectional robust z-score using median and MAD
```

Rules:

- default population is the C1 point-in-time eligible universe for that date;
- insufficient population must produce null values and a reported reason;
- ties must use a documented deterministic ranking method;
- rank direction must be documented;
- robust z-score behaviour when MAD is zero must be explicit;
- no normalization may use statistics from another date.

### 10.6 Market-context features

C3 may derive market context from the daily stock panel only, for example:

```text
equal-weight eligible-universe return
median eligible-universe return
fraction of eligible symbols with positive return
cross-sectional return dispersion
eligible symbol count
```

These features must be computed from the point-in-time universe for each date and joined back to eligible rows for that date.

Direct use of `market_quotes` or another production table is out of scope unless first extracted and audited through a separate C1 extension or later contract.

## 11. Warm-up, null, and infinity policy

C3 must not impute feature values with future data.

Required rules:

- preserve null during insufficient lookback;
- never backward-fill;
- forward-fill only when a specific feature definition explicitly permits it; default is no forward-fill;
- replace positive/negative infinity with null and report the cause;
- preserve a distinction between insufficient history, invalid source denominator, absent observation, and insufficient cross-sectional population;
- do not drop an entire row merely because one feature is null;
- do not globally drop symbols with short listing histories;
- newly listed symbols become usable feature-by-feature as their required history accumulates.

The output should include compact quality metadata or companion columns sufficient to reproduce aggregate reasons for missing feature values without creating an uncontrolled number of flags.

## 12. Point-in-time universe handling

C3 must join feature rows to C1’s point-in-time universe by exact:

```text
trade_date, symbol
```

It must not:

- use the latest eligible-symbol list for earlier dates;
- fill a missing historical eligibility record using a later value;
- infer eligibility from a symbol’s eventual survival;
- include delisted or not-yet-listed symbols before valid observations exist;
- use future volume or turnover to establish current eligibility.

The pipeline may output:

1. a full observed-panel feature table with an eligibility flag; and/or
2. an eligible-only feature table.

If both are generated, their purposes and counts must be reconciled in the manifest. The recommended canonical research output is the full observed panel with exact point-in-time eligibility retained as a column, allowing later contracts to apply different policies without recomputing primitive features.

## 13. Determinism and ordering

For the same:

- C1 input file bytes;
- C1 manifests;
- feature configuration;
- feature registry version;
- code Git revision; and
- dependency environment,

C3 must produce logically identical output.

Requirements:

- explicit deterministic sorting;
- stable feature-column ordering;
- stable manifest ordering;
- stable symbol ordering;
- no dependence on filesystem traversal order;
- no random sampling;
- no timestamp inside the logical content hash;
- floating-point precision policy recorded;
- deterministic Parquet-writing options documented.

Because Parquet file bytes may vary across library versions or metadata timestamps, C3 must define both:

- a file hash; and
- a logical-content hash based on canonical ordered values/schema.

Two consecutive exports in the same environment must produce matching logical-content hashes. Prefer matching file hashes as well when feasible.

## 14. Output schema

The canonical feature table must contain at least:

```text
trade_date
symbol
point_in_time_eligible
source_observation_present
feature columns in registry order
```

Optional useful columns:

```text
listing_age_observations
days_since_previous_observation
feature_quality_mask
```

Raw OHLCV columns should not be duplicated into the canonical feature table unless needed for traceability. The manifest must identify the source dataset and exact input columns.

Key requirements:

- unique `(trade_date, symbol)`;
- deterministic ascending ordering by `trade_date, symbol` or explicitly documented equivalent;
- stable dtypes;
- no object/untyped columns;
- no infinities;
- finite/non-null counts reported per feature;
- feature columns exactly match the registry and manifest.

## 15. Feature manifest

Each extraction must generate a small machine-readable manifest containing at least:

```text
manifest version
feature-set name and version
generation timestamp UTC
code Git commit and dirty state
input daily Parquet path and hash
input universe Parquet path and hash
input C1 manifest path and hash
input maximum trade date
input row count and symbol count
output row count and symbol count
output date range
output file hash
logical-content hash
ordered feature list
feature-registry hash
configuration and configuration hash
raw/adjusted field policy
point-in-time universe methodology
availability convention
window definitions
minimum-history rules
null/infinity policy
float precision
package versions
```

The timestamp must not be included in the logical-content hash.

## 16. Feature quality report

Generate:

```text
artifacts/reports/C3_FEATURE_REPORT.md
```

It must include at least:

- input snapshot identity;
- feature-set identity;
- row, symbol, and date coverage;
- point-in-time eligible counts by date summary;
- per-feature non-null count and percentage;
- warm-up null counts;
- invalid-denominator null counts;
- infinity count before sanitation and zero infinity count after sanitation;
- selected percentiles and extreme-value summaries;
- stale/missing-history interactions;
- cross-sectional population-size distribution;
- raw/adjusted field policy;
- adjusted-series limitation inherited from C1;
- confirmation that open/close outside high/low were preserved;
- deterministic export evidence;
- known limitations and recommendations for the next contract.

The report must not include target correlations, feature importance, model accuracy, backtest results, or profitability claims.

## 17. CLI or pipeline entry point

Provide a reproducible command such as:

```bash
python -m psx_ml.features.pipeline \
  --config config/features.toml
```

or an equivalent console script.

Required behaviour:

- validates input manifests before processing;
- refuses output paths inside `psx-stock-watcher`;
- refuses the production database path;
- supports temporary output locations for tests;
- creates parent output directories only inside the research project or supplied temporary test directories;
- writes output atomically where practical;
- does not leave a partially accepted output if generation fails;
- emits a concise completion summary and manifest path.

## 18. Testing strategy

Tests should use small synthetic panels with known expected values. They must not depend on the live production database.

Synthetic fixtures must cover:

- multiple symbols;
- irregular listing starts;
- a delisting/end-of-history case;
- absent exchange observations;
- zero and null volume;
- nonpositive denominator values;
- stale closes;
- open and close outside high/low;
- high below low as a strict invalid case;
- changing point-in-time universe eligibility;
- cross-sectional ties;
- insufficient cross-sectional population;
- adjusted and raw field families where supported.

Property-style tests should verify that appending future rows does not alter any existing historical feature values.

## 19. Acceptance tests

C3 is accepted only when all of the following pass.

### AT-C3-01 — Isolated branch

Implementation is committed on `feature/c3-point-in-time-features`, based on accepted C2 `main`, with no changes to `psx-stock-watcher` or C14.

### AT-C3-02 — Research-artifact-only inputs

The feature pipeline reads C1 Parquet/manifests and makes zero SQLite connections. A test must monkeypatch or otherwise canary `sqlite3.connect` and prove no call occurs.

### AT-C3-03 — Input reconciliation

Input row counts, key uniqueness, schema, symbol count, date range, and supported manifest version are validated before feature generation.

### AT-C3-04 — Unique output keys

The feature table contains no duplicate `(trade_date, symbol)` rows.

### AT-C3-05 — Trailing-only rolling values

Known synthetic examples prove each rolling feature uses only the current and prior observations for that symbol.

### AT-C3-06 — Future-append invariance

Appending one or more future dates to an input panel does not change any previously generated feature value or eligibility value.

### AT-C3-07 — Symbol isolation

Adding or changing future/history rows for one symbol does not alter another symbol’s symbol-level features.

### AT-C3-08 — Current-date availability semantics

Features using session `D` OHLCV are documented and marked as available only after the close of `D`; tests prevent any negative shift or future-row lookup.

### AT-C3-09 — Point-in-time universe safety

Eligibility for date `D` comes only from the exact C1 universe record for `D`. Today’s eligible list cannot appear retrospectively.

### AT-C3-10 — Cross-sectional date isolation

Cross-sectional ranks and normalizations for date `D` use only the permitted population for date `D`.

### AT-C3-11 — Cross-sectional deterministic ties

Tie handling is documented and produces deterministic results independent of input row order.

### AT-C3-12 — Raw/adjusted consistency

Every feature declares its field family, and automated tests fail if raw price is paired with adjusted volume or another prohibited mixed-family formula.

### AT-C3-13 — Open/close PSX convention preserved

Rows with open or close outside high/low remain present and produce features according to documented formulas. They are not clipped or rejected solely for that condition.

### AT-C3-14 — Strict impossible range handling

Rows with `high < low` are flagged or masked according to policy and reported reproducibly.

### AT-C3-15 — Missing observation distinction

An absent symbol/date observation is not converted to a stored zero-volume row. Zero volume, null volume, and absent observation remain distinguishable.

### AT-C3-16 — Listing-history safety

A newly listed symbol has null features until each feature’s own minimum observation requirement is reached; no future backfill occurs.

### AT-C3-17 — Stale-price reproducibility

Stale-close run length and trailing unchanged-close metrics match known synthetic expectations.

### AT-C3-18 — Gap-awareness

`days_since_previous_observation` or equivalent gap metadata is correct, and observation-count returns do not falsely claim calendar-day spacing.

### AT-C3-19 — Division and infinity safety

Zero/nonpositive denominators never produce retained infinity. Resulting nulls and reasons are reported deterministically.

### AT-C3-20 — Feature registry completeness

Every output feature appears exactly once in the registry and manifest with required metadata. No undocumented feature column is emitted.

### AT-C3-21 — Stable schema and ordering

Output row order, feature-column order, dtypes, and manifest ordering are deterministic.

### AT-C3-22 — Deterministic export

Two consecutive runs on the same input/configuration produce identical logical-content hashes and reconciled row/feature counts.

### AT-C3-23 — Manifest reconciliation

Manifest output row count, symbol count, date range, feature list, and hashes agree with the generated Parquet file.

### AT-C3-24 — Temporary test outputs

All tests write only to `tmp_path` or equivalent temporary directories and do not modify project caches, reports, production data, or watcher files.

### AT-C3-25 — Output-boundary enforcement

The pipeline refuses output locations inside `psx-stock-watcher`, refuses the production database path, and never writes outside approved research or temporary directories.

### AT-C3-26 — CPU-only operation

The complete C3 suite and feature generation work with CUDA hidden. C3 does not require GPU availability.

### AT-C3-27 — Feature report completeness

The Markdown report includes coverage, null reasons, extreme summaries, field policy, point-in-time methodology, PSX open/close convention, adjusted-series limitation, and deterministic-export evidence.

### AT-C3-28 — Scope guard

Repository changes introduce no targets, future returns, dataset splits, model fitting, predictions, signals, portfolio logic, transaction-cost logic, or backtests.

### AT-C3-29 — Source fingerprints unchanged

Where live acceptance is performed, before/after fingerprints of `psx_watcher.db` and watcher repository state remain unchanged.

### AT-C3-30 — Full suite passes

All C1, C2, and C3 tests pass together in the dedicated `psx-ml-research` environment.

## 20. Live acceptance procedure

Suggested acceptance sequence:

```bash
conda activate psx-ml-research
cd ~/psx-ml-research

git status --short
git branch --show-current

python -m pip install -e '.[dev]'
python -m pytest -s

python -m psx_ml.features.pipeline \
  --config config/features.toml

python -m psx_ml.features.pipeline \
  --config config/features.toml
```

Record:

- branch name;
- Git commit;
- test results;
- input hashes;
- output file hash;
- logical-content hash for both runs;
- output counts and date range;
- feature count;
- source database and watcher fingerprints before/after.

## 21. Delivery artifacts

C3 delivery must include:

```text
contracts/C3_POINT_IN_TIME_FEATURE_ENGINEERING/CONTRACT.md
config/features.example.toml
feature registry/catalog
feature pipeline implementation
C3 tests
feature-manifest schema/example
artifacts/reports/C3_FEATURE_REPORT.md
artifacts/reports/C3_DELIVERY.md
```

The delivery report must map every acceptance test to concrete evidence.

## 22. Architecture review decisions

The following decisions are part of this contract:

1. **C3 consumes C1 research Parquet, not live SQLite.** This reduces accidental production coupling and makes the input snapshot explicit.
2. **C3 is CPU-first.** The RTX 5070 is reserved for workloads that can materially benefit from it; daily panel feature engineering should remain portable and easy to test.
3. **Features are available after the current session closes.** Later target and execution contracts must shift decisions forward accordingly.
4. **Primitive, interpretable features come before indicator proliferation.** C3 avoids dozens of highly correlated TA-library defaults.
5. **Point-in-time eligibility is retained per row.** The latest universe is never projected backward.
6. **Missing observations are not synthesized.** No fake zero-volume candles are created.
7. **PSX open/close outside high/low is preserved.** It is treated as a documented source convention, not an automatic row failure.
8. **Adjusted-data limitations remain visible.** Algebraic consistency is not misrepresented as proof of total-return accuracy.
9. **No target-informed feature choice is allowed.** Feature selection belongs after target, split, and evaluation contracts exist.
10. **C3 does not establish profitability.** It establishes a trustworthy point-in-time feature layer.

## 23. Completion condition

C3 is complete only when:

- all acceptance tests pass;
- the feature table and manifest reconcile;
- repeated runs are deterministic;
- the feature report documents limitations honestly;
- source-system fingerprints remain unchanged;
- the delivery report is reviewed and accepted; and
- the feature branch is merged into `main` only after acceptance.

Do not proceed to target construction, dataset splitting, model training, prediction generation, or backtesting within C3.
