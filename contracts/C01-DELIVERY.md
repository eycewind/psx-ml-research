# C1 — Delivery and Acceptance Report

## Delivery summary

C1 implements hardened read-only SQLite access, live-schema validation, source
documentation, reproducible quality and adjustment audits, listing/gap history,
stale-close analysis, a trailing-only liquid-universe proposal, deterministic
Parquet extraction, provenance manifests, Markdown reporting, and write-safety
canaries. It contains no features, indicators, targets, models, predictions, or
backtests.

## Live findings

- `daily_ohlc`: 621,794 rows, 821 symbols, 1,615 trade dates,
  2020-01-01 through 2026-07-10; zero duplicate primary keys.
- 5,799 raw and adjusted opens are null.
- 2,701 rows have a nonpositive raw high/low/close; 5,401 adjusted price values
  are nonpositive.
- 393 raw and adjusted opens are outside high/low.
- 17,561 closes are outside high/low and intentionally reported separately.
- No missing/zero/negative stored volumes in this snapshot; upstream omitted
  zero-volume rows.
- 47,680 unchanged-close transitions and 1,682 runs reaching five observations.
- 566 of 821 symbols have at least one absent exchange date between their first
  and last observations; median within-span missing rate is 9.9752%.
- Adjustment-factor price and reciprocal-volume equations have zero mismatches
  at relative tolerance 1e-6, but this does not validate dividend treatment or
  resolve source-documented adjusted-series quarantine concerns.
- The initial proposal marks 307 symbols eligible on 2026-07-10. Eligibility is
  computed independently for every date from no more than 60 observations
  ending on that date.

## Acceptance evidence

Synthetic acceptance suite:

```text
$ .venv/bin/pytest
.....                                                                    [100%]
5 passed in 0.61s
```

Two consecutive exports of the same live snapshot produced identical hashes:

```text
7a6c0cbdeef66adb2ad87a7f29c5ca80559190440b4547c78154f842e834c02e  daily_ohlcv.parquet
94c68a383681999749c1c50c6c98b075fc96c4b69d55999a4439273c34aa1eb7  point_in_time_universe.parquet
```

Manifest/export reconciliation: both exports contain 621,794 rows; the daily
manifest reports 821 sorted symbols and range 2020-01-01 through 2026-07-10.

Production safety fingerprint before and after all live work:

```text
DB SHA-256: e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b
DB size:    304885760
DB mtime:   1785003631
Watcher HEAD: 404e3637637ca89d4455b9f7069c6191a3658d83
Watcher porcelain status: <empty>
```

The values were unchanged. The connection tests also prove DML and DDL fail
after an attempted `query_only=OFF`, and missing database paths are not created.

## Deviations and judgments

- The corrected source/project prefix `/home/hassan/` and watcher name
  `psx-stock-watcher` supersede the original `/media/ata/.../stock-watcher` paths.
- Zero-volume analysis necessarily distinguishes stored zero counts (zero) from
  absent observations because the upstream backfill discarded zero-volume rows.
- Close-outside-range is a soft metric, not an impossible-OHLC failure, based on
  inspected watcher documentation about closing-auction semantics.
- Source `universe` and `tradeable_universe` were not reused because the former
  is not point-in-time and independent reproducibility is a C1 requirement.
- The project uses PyArrow directly rather than pandas to keep C1 extraction
  narrow and deterministic.
- No production source was copied into Git. Generated Parquet, JSON audit/schema
  reports, caches, databases, and model artifacts are ignored; the small
  manifest contract/example and Markdown audit report remain tracked.

## Acceptance decision

Accepted for C1. C2 remains explicitly out of scope.
