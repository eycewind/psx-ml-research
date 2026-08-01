# C3 Point-in-Time Feature Report

Feature set `psx_daily_primitives` v1 from C1 input `7a6c0cbdeef66adb2ad87a7f29c5ca80559190440b4547c78154f842e834c02e`.

## Coverage

- Rows: 621,794
- Symbols: 821
- Dates: 2020-01-01 through 2026-07-10
- Features: 27
- PIT eligible rows: 305,267

## Field and timing policy

adjusted price OHLC and adjusted volume are paired consistently; raw fields are not mixed into formulas

Features for D use observations through D and are available only after market close on D; earliest decision is the next session

Adjusted prices and volume are algebraically consistent with C1 factors, but C1 did not establish complete dividend adjustment or universal adjusted-series reliability. These features must not be described as verified total returns.

## Quality

- Strict `high < low` rows flagged/masked in range calculations: 0
- Stored null-volume rows: 0
- Stored zero-volume rows: 0
- Infinity values before sanitation: 0
- Infinity values after sanitation: 0
- Eligible population per date: min 0, median 183, max 315

Open or close outside high/low rows are preserved without clipping or rejection. Only strict high-below-low rows mask true-range calculations. Missing observations are never synthesized as zero-volume candles; observation-count lookbacks and calendar-day gap metadata remain distinct.

## Per-feature coverage, null reasons, and selected percentiles

`Other null` means an invalid denominator/source value or insufficient permitted cross-sectional population after warm-up and ineligible-population nulls are removed.

| Feature | Non-null | Coverage | Warm-up null | Ineligible null | Other null | p01 | Median | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `ret_1obs_adj` | 620,973 | 99.87% | 821 | 0 | 0 | -0.0986421 | 0 | 0.107143 |
| `ret_5obs_adj` | 617,869 | 99.37% | 3,925 | 0 | 0 | -0.196559 | -0.000555092 | 0.345289 |
| `ret_20obs_adj` | 607,177 | 97.65% | 14,617 | 0 | 0 | -0.315044 | 0.000996018 | 0.782322 |
| `log_ret_1obs_adj` | 620,973 | 99.87% | 821 | 0 | 0 | -0.103853 | 0 | 0.101783 |
| `log_ret_20obs_adj` | 607,177 | 97.65% | 14,617 | 0 | 0 | -0.3784 | 0.000995522 | 0.577917 |
| `close_to_open_1obs_adj` | 615,995 | 99.07% | 0 | 0 | 5,799 | -0.10414 | 0 | 0.119918 |
| `open_gap_1obs_adj` | 615,261 | 98.95% | 821 | 0 | 5,712 | -0.0994854 | 0.00125154 | 0.100037 |
| `close_to_mean_20obs_adj` | 607,826 | 97.75% | 13,968 | 0 | 0 | -0.20348 | -0.00102689 | 0.365502 |
| `close_to_max_20obs_adj` | 607,826 | 97.75% | 13,968 | 0 | 0 | -0.352665 | -0.0613725 | 0 |
| `log1p_volume_adj` | 621,794 | 100.00% | 0 | 0 | 0 | 2.3979 | 10.7284 | 17.1456 |
| `volume_ratio_median_20obs_adj` | 607,826 | 97.75% | 13,968 | 0 | 0 | 0.0166667 | 0.996549 | 39.3429 |
| `turnover_1obs_adj` | 621,794 | 100.00% | 0 | 0 | 0 | 649.614 | 1.38712e+06 | 1.11969e+09 |
| `turnover_median_20obs_adj` | 607,826 | 97.75% | 13,968 | 0 | 0 | 4118.39 | 1.20002e+06 | 7.52765e+08 |
| `rv_20obs_adj` | 607,177 | 97.65% | 14,617 | 0 | 0 | 0.00488698 | 0.0294979 | 0.0999153 |
| `true_range_1obs_adj` | 620,973 | 99.87% | 821 | 0 | 0 | 0 | 1.13 | 100 |
| `atr_mean_20obs_adj` | 607,177 | 97.65% | 14,617 | 0 | 0 | 0.068 | 1.3475 | 94.3819 |
| `amihud_mean_20obs_adj` | 607,177 | 97.65% | 14,617 | 0 | 0 | 2.49692e-11 | 2.06188e-08 | 1.34182e-05 |
| `stale_close_run_length` | 621,794 | 100.00% | 0 | 0 | 0 | 0 | 0 | 3 |
| `unchanged_close_fraction_20obs` | 607,826 | 97.75% | 13,968 | 0 | 0 | 0 | 0 | 0.65 |
| `days_since_previous_observation` | 620,973 | 99.87% | 821 | 0 | 0 | 1 | 1 | 10 |
| `strict_high_below_low_flag` | 621,794 | 100.00% | 0 | 0 | 0 | 0 | 0 | 0 |
| `missing_volume_flag` | 621,794 | 100.00% | 0 | 0 | 0 | 0 | 0 | 0 |
| `zero_volume_flag` | 621,794 | 100.00% | 0 | 0 | 0 | 0 | 0 | 0 |
| `ret_20obs_rank_adj` | 305,267 | 49.09% | 0 | 316,527 | 0 | 0.00706714 | 0.5 | 0.992933 |
| `turnover_rank_adj` | 305,267 | 49.09% | 0 | 316,527 | 0 | 0.00706714 | 0.5 | 0.992933 |
| `market_median_ret_1obs_adj` | 305,267 | 49.09% | 0 | 316,527 | 0 | -0.046998 | -0.000822368 | 0.0392615 |
| `eligible_symbol_count` | 305,267 | 49.09% | 0 | 316,527 | 0 | 127 | 196 | 313 |

## Stale and history behavior

Stale-close run length and trailing unchanged-close fraction operate on stored observations. Newly listed and ragged histories warm up feature-by-feature; no backward fill, future interpolation, or global short-history deletion occurs. `days_since_previous_observation` reports calendar gaps while returns retain observation-count names.

## Determinism and provenance

- Output file SHA-256: `0da1b030197519eb01c8623cc4bd3e542c275167e6a7bb89b84c15d01181e9aa`
- Logical-content SHA-256: `1fe2376f7690152a078115b5c7548b9d6e960a5e394fbe29162a8b314d310b83`
- Registry SHA-256: `593ee776651dd06170e8f145ff9df7fb8730e749dc4a06b7f1170e9768da3403`
- Configuration SHA-256: `5aa17f16b0dc03fe4018e685e9fe1e0c4f9059f3ecb3c078910714cf9313af11`

The logical hash excludes generation time and is computed from canonical ordered Arrow values and schema. Repeated live execution evidence is recorded in C3 delivery.

## Known limitations and next-contract guidance

These are transparent primitives, not target-selected predictors. No claims about predictive value or profitability are made. Later target/execution work must treat each row as available only after its session close and may act no earlier than the following trading session.
