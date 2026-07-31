# C1 Data Foundation and Audit Report

Generated from `/home/hassan/psx-stock-watcher/data/psx_watcher.db` in enforced read-only mode.

## Coverage

- Rows: 621,794
- Symbols: 821
- Trade dates: 1,615
- Range: 2020-01-01 through 2026-07-10
- Duplicate symbol-dates: 0

## Canonical fields

Raw OHLCV: `open`, `high`, `low`, `close`, `volume`. Adjusted fields: `open_adj`, `high_adj`, `low_adj`, `close_adj`, `volume_adj`, governed by `adj_factor`. Both are exported; adjusted integrity exceptions are not hidden.

## Quality metrics

| Metric | Count |
|---|---:|
| `adjusted_high_below_low` | 0 |
| `adjusted_open_outside_range` | 393 |
| `adjusted_price_factor_mismatch` | 0 |
| `adjusted_volume_factor_mismatch` | 0 |
| `close_outside_range` | 17,561 |
| `high_below_low` | 0 |
| `invalid_dates` | 0 |
| `invalid_open_missing_flag` | 0 |
| `missing_volume` | 0 |
| `negative_volume` | 0 |
| `nonpositive_adj_factor` | 0 |
| `nonpositive_adjusted_price` | 5,401 |
| `nonpositive_raw_price` | 2,701 |
| `null_adj_factor` | 0 |
| `open_missing_inconsistent` | 0 |
| `open_outside_range` | 393 |
| `stale_close_transitions` | 47,680 |
| `stale_runs_at_least_threshold` | 1,682 |
| `zero_volume` | 0 |

## Null counts

| Field | Count |
|---|---:|
| `trade_date` | 0 |
| `symbol` | 0 |
| `open` | 5,799 |
| `high` | 0 |
| `low` | 0 |
| `close` | 0 |
| `volume` | 0 |
| `ldcp` | 0 |
| `open_adj` | 5,799 |
| `high_adj` | 0 |
| `low_adj` | 0 |
| `close_adj` | 0 |
| `volume_adj` | 0 |
| `adj_factor` | 0 |

## Missing and listing histories

Histories are bounded by each symbol's first and last observation. 821 symbols were assessed; 566 have gaps within their observed listing span; median missing rate is 9.9752%.

## Point-in-time liquid universe proposal

For each observed symbol-date D, use at most the last 60 observations through D; require at least 40 observations, median raw close*volume of at least PKR 1,000,000, and unchanged-close fraction no greater than 20%. No row after D is consulted.

The proposal marks 305,267 observed symbol-dates eligible; 307 symbols are eligible on the latest observed date (2026-07-10).

The calculation consumes observations in ascending date order and never consults a future row. The current/as-of-now watcher `universe` table is deliberately not used.

## Extraction provenance

- Source SHA-256: `e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b`
- Daily Parquet: 621,794 rows, `7a6c0cbdeef66adb2ad87a7f29c5ca80559190440b4547c78154f842e834c02e`
- PIT universe: 621,794 rows, `94c68a383681999749c1c50c6c98b075fc96c4b69d55999a4439273c34aa1eb7`

## Interpretation cautions

A close outside high/low is reported separately because the source documentation attributes this to PSX closing-auction behavior, an inference still awaiting authoritative verification. Zero-volume rows were omitted upstream, so missing observations cannot automatically be classified as data loss. Cash-dividend adjustment is not established by this dataset.
