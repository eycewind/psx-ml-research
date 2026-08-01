# C6 Classification Correction Delivery

## Status

The classification traceability correction is complete. Remaining C6 robust evaluation work is not represented as complete by this report.

## Changes

- Added exact `classification_rule` provenance to every classification interval.
- Audited counts by type, source, confidence, rule, and observed sector.
- Added deterministic sector and competing-rule Parquet diagnostics.
- Added a targeted manual-review queue using structural flags, fixed C5 loss concentration, and development-period extreme targets.
- Preserved classifier precedence and universe membership pending stronger evidence.

## Snapshot findings

- Generic low-confidence `sector_prefix:08`: 584 intervals.
- Exact sector mappings: 63 intervals.
- Unknown intervals: 0.
- Competing-rule intervals: 271.
- Manual-review symbols: 591.
- Review reasons: `{"classification_rule_conflict": 269, "extreme_c4_target": 350, "multiple_classification_intervals": 33, "short_interval_or_maturity_like_ticker": 144, "special_security_entered_pit_universe": 24, "top_c5_squared_loss": 16, "unusual_prefix_inferred_equity": 35}`.

Zero unknowns arise because every otherwise unmatched interval in this snapshot has an observed sector beginning with `08`; zero does not imply authoritative coverage.

The C5 negative linear conclusion is unchanged. No robust-metric reinterpretation, profitability analysis, nonlinear model, signal, portfolio, execution, or backtest is introduced by this correction.

## Verification

- Complete CPU-only suite with CUDA hidden: **57 passed, 1 expected GPU skip in 9.01 seconds**.
- Two consecutive live correction runs reproduced the same logical hashes recorded in `C6_MANIFEST.json`.
- Final holdout accessed: **false**.
- Production DB SHA-256: `e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b`.
- Watcher HEAD: `404e3637637ca89d4455b9f7069c6191a3658d83`; porcelain status empty.
