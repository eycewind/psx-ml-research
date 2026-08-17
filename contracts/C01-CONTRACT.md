# C1 — Data Foundation and Audit Contract

## Purpose and boundaries

C1 establishes a trustworthy, reproducible, point-in-time-safe research data
foundation from `/home/hassan/psx-stock-watcher/data/psx_watcher.db`. The
watcher repository and database are immutable inputs. C1 does not implement
technical indicators, features, targets, models, training, predictions, or
backtesting, and it does not modify or merge the watcher C14 branch.

All source access MUST use `file:<absolute-path>?mode=ro`, `uri=True`, and
`PRAGMA query_only=ON`. Research outputs MUST resolve beneath this repository.
Tests MUST use temporary databases and output directories.

## Inspected source contract

Live inspection on 2026-07-31 found `daily_ohlc` to be the canonical daily
table: primary key `(trade_date, symbol)`, 621,794 rows, 821 symbols, 1,615
dates, 2020-01-01 through 2026-07-10. Canonical raw fields are `open`, `high`,
`low`, `close`, `volume`; canonical adjusted fields are `open_adj`, `high_adj`,
`low_adj`, `close_adj`, `volume_adj`, with `adj_factor`. `sector`, `ldcp`,
`open_missing`, and `source` are retained provenance/context fields.

Adjusted fields are not uniformly reliable merely because they are populated.
The source handoff documents 774 quarantined/unreliable adjusted-close names.
C1 therefore exports raw and adjusted values together and reports row-level
integrity flags; it does not silently replace raw values. Cash dividends are
not adjusted reliably by the source.

Material source properties:

- zero-volume source rows were dropped during watcher ingestion, so missing
  symbol-days encode both non-trading and listing-history effects;
- official auction closes may lie outside continuous-session high/low and are
  reported as `close_outside_range`, not automatically called impossible;
- missing raw opens are represented by `open IS NULL` and `open_missing=1`;
- the source `universe` table is as-of-now and is forbidden for retrospective
  eligibility; source `tradeable_universe` is also not an extraction input;
- `market_quotes` has zero rows in the inspected snapshot.

## Architecture and deliverables

- `psx_ml.data.sqlite`: reusable hardened read-only connection and schema
  introspection.
- `psx_ml.validation.audit`: reproducible source metrics, invalid dates,
  duplicates, null/invalid values, zero/missing volume, stale runs, ragged and
  listing histories, OHLC rules, and adjustment integrity.
- `psx_ml.universe.point_in_time`: daily eligibility using only the current and
  preceding configured observations. Initial proposal: 60-session trailing
  window, at least 40 observations, median raw `close * volume` >= PKR 1m, and
  stale-close fraction <= 20%. This is a research proposal, not a trading rule.
- `psx_ml.data.extract`: ordered deterministic Parquet exports and manifest.
- `psx_ml.reporting`: Markdown audit generation.
- `contracts/.../DELIVERY.md`: real acceptance evidence and deviations.

The daily export is sorted by `(trade_date, symbol)`. Universe output contains
one row per observed symbol-date, with trailing window start/end, observation
count, median turnover, stale fraction, eligibility and reason. Calculations at
date D may use rows with `trade_date <= D` only.

## Audit definitions

- Duplicate: more than one row for `(trade_date, symbol)`.
- Invalid date: not exactly a valid ISO Gregorian `YYYY-MM-DD` value.
- Impossible raw OHLC: nonpositive high/low/close; high < low; or a present open
  outside `[low, high]`. A close outside the range is counted separately.
- Null/missing: per-column null counts plus `open_missing` consistency.
- Missing volume: `volume IS NULL`; zero/negative volume are separate metrics.
- Stale price: unchanged raw close versus the symbol's preceding observed row;
  runs of at least configured length are summarized. This does not claim the
  symbol traded on absent market dates.
- Missing/listing history: first/last observed date, observed rows, exchange
  dates within that interval, and absent-date count/rate.
- Adjustment integrity: null/nonpositive factors, nonpositive adjusted values,
  raw-to-adjusted price ratios inconsistent with `adj_factor`, volume ratio
  inconsistent with reciprocal factor, and adjusted OHLC rules. Tolerance is
  configuration-controlled.

## Manifest contract

The version-controlled manifest schema/example documents: source database
path, extraction UTC timestamp, maximum source trade date, source row count,
symbols included and count, date range, literal SQL/extraction definition,
code/Git version, adjusted/raw selection, universe methodology/configuration,
source database SHA-256, config SHA-256, output row counts, file SHA-256 values,
and Arrow/Python versions. Runtime manifests accompany ignored data locally;
small provenance examples remain version-controlled.

## Acceptance tests

1. A valid source opens with URI `mode=ro`; a missing path does not get created.
2. `INSERT`, DDL, and attempts to disable `query_only` cannot write through the
   research connection.
3. Production DB SHA-256, size, mtime, watcher Git HEAD/status, and tracked-file
   diff remain unchanged before versus after acceptance.
4. Schema documentation names `daily_ohlc` and the raw/adjusted selections.
5. Duplicate `(trade_date, symbol)` groups are reproducibly detected.
6. Invalid dates, impossible open/high/low relationships, and soft
   close-outside-range cases are reported separately.
7. Null, zero/negative/missing volume, stale-price, history-gap metrics reproduce.
8. Adjustment-factor and adjusted OHLC integrity violations reproduce.
9. A future-row canary cannot change eligibility on any earlier date.
10. Two exports of the same snapshot/config produce identical Parquet SHA-256.
11. Manifest row counts, date range, symbols, and hashes reconcile with files.
12. Tests write only beneath pytest temporary directories and compare production
    fingerprints read-only.

Acceptance command: `pytest`, followed by a production C1 run and a second
production fingerprint comparison. Any failure is a C1 rejection.
