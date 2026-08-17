# C3 Delivery and Acceptance Report

## Delivery summary

C3 delivers a deterministic CPU-only point-in-time feature pipeline consuming
only C1-controlled Parquet and manifest artifacts. The canonical full observed
panel retains exact C1 eligibility and contains 621,794 unique symbol-date rows,
821 symbols, 27 registered primitive features, and coverage through 2026-07-10.

Branch: `feature/c3-point-in-time-features`. Implementation commit: `1adddb3`.
Live feature-report commit: `4492d47`.

## Feature and policy decisions

- Adjusted OHLC and adjusted volume are paired consistently for v1; raw-family
  generation is also implemented and tested as a separate explicit policy.
- Feature rows use information through close D and are available only after
  close D. The earliest downstream decision is the next session.
- Lookbacks are stored-observation counts, not calendar-day claims.
- No missing symbol-date is synthesized. Stored zero and null volume have
  separate flags; calendar gaps use `days_since_previous_observation`.
- Open/close outside high/low are preserved. Only `high < low` masks true range.
- Cross-sectional features use exact-date eligible rows, stable average-tie
  percentile ranks, and a configured minimum population.
- The output is the full observed panel; PIT eligibility remains a column.
- Adjusted arithmetic does not establish dividends or universal adjusted-series
  reliability, and the report explicitly preserves that C1 limitation.

## Live output and determinism

Two clean runs in the same accepted C2 environment produced:

```text
rows:                 621794
symbols:              821
features:             27
PIT eligible rows:    305267
date range:           2020-01-01 through 2026-07-10
Parquet SHA-256:      0da1b030197519eb01c8623cc4bd3e542c275167e6a7bb89b84c15d01181e9aa
logical SHA-256:      1fe2376f7690152a078115b5c7548b9d6e960a5e394fbe29162a8b314d310b83
```

Both file and logical hashes matched. The tracked provenance manifest records
the second clean generation at `4492d47` with `dirty=false`. Runtime output
remains under ignored `data/processed/features/`.

## Acceptance mapping

| Tests | Evidence |
|---|---|
| AT-C3-01 branch | Based on accepted C2 main; isolated required feature branch |
| AT-C3-02 source type | Pipeline accepts only Parquet/JSON paths; SQLite-connect canary records zero calls |
| AT-C3-03 reconciliation | Manifest version, hashes, rows, symbols, range, schema, and unique keys validated before calculation |
| AT-C3-04 keys | Synthetic and live outputs reconcile to unique `(trade_date,symbol)` |
| AT-C3-05–08 trailing/timing/isolation | Known-value, future-append, symbol-isolation tests; registry availability convention forbids same-session decisions |
| AT-C3-09–11 universe/cross-section | Exact-key eligibility, date-only population, stable merge-sort average ties tested with reversed input |
| AT-C3-12 family consistency | Mixed config rejected; separate raw-family test proves raw turnover uses raw price and volume |
| AT-C3-13–15 PSX/missing rules | Outside-range open preserved; high-below-low masks range; null/zero/absent states remain distinct |
| AT-C3-16–18 listing/stale/gaps | Per-feature warm-up, stale run, unchanged fraction, and irregular calendar gap tests pass |
| AT-C3-19 infinity | Nonpositive denominators yield null; live before/after infinity counts are zero |
| AT-C3-20–23 registry/schema/export/manifest | Registry equals ordered output columns; stable dtypes/order; two hashes match; manifest reconciles |
| AT-C3-24–25 isolation/boundaries | Tests use `tmp_path`; watcher/database/outside paths rejected |
| AT-C3-26 CPU | Complete suite run with `CUDA_VISIBLE_DEVICES=""` |
| AT-C3-27 report | Coverage, null reasons, extremes, PIT policy, PSX conventions, adjustment limitation, and hashes included |
| AT-C3-28 scope | No targets, future returns, splits, fitting, predictions, signals, portfolio, costs, or backtests |
| AT-C3-29 source safety | Before/after database/watcher fingerprints below match |
| AT-C3-30 full suite | 27 passed, 1 expected C2 GPU skip in the first final CPU run |

## Source-system safety

Before C3 and after both live runs:

```text
DB SHA-256: e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b
DB size: 304885760
DB mtime: 1785003631
Watcher HEAD: 404e3637637ca89d4455b9f7069c6191a3658d83
Watcher porcelain status: <empty>
```

C3 never opened the database. Live input was the C1 daily and universe Parquet
snapshot with hashes `7a6c0cbd…34c02e` and `94c68a38…aa1eb7`.

## Deviations and judgments

- The contract suggested several candidate primitives. V1 deliberately selects
  27 transparent features rather than implementing every candidate.
- Feature-set v1 strictly accepts return windows `[1,5,20]` and rolling windows
  `[5,20,60]`; a value-changing window expansion requires a new feature-set or
  registry version rather than silently changing current columns.
- C1 exposes no per-row adjusted-series quarantine field. C3 therefore preserves
  the limitation prominently in the manifest/report rather than inventing a
  usability classification.
- Cross-sectional and market-context values are null on ineligible rows while
  symbol primitives remain available across the observed panel.
- A tracked manifest copy lives in `artifacts/reports/`; the configured runtime
  manifest remains alongside the ignored feature Parquet under `data/processed`.
- PyArrow/NumPy CPU calculations were chosen; C3 does not import or require
  PyTorch and was accepted with CUDA hidden.

## Scope statement and recommendation

C3 introduced no targets, future-return labels, dataset splits, model classes,
training, prediction, signals, portfolio construction, transaction costs,
execution simulation, backtesting, or profitability claims. The pending watcher
C14 branch was untouched.

C3 is recommended for review and acceptance. Do not merge before that review.
