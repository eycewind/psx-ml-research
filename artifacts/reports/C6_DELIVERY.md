# C6 Security-Master Direction Delivery

## Status

The classification evidence direction now uses a dated PSX master first. Remaining C6 robust evaluation work is not represented as complete by this report.

## Changes

- Inspected the live Listings, Eligible Scrips, Fixed Income, company, ETF, and debt routes and recorded their endpoints.
- Added the versioned `psx_security_master_2026-08-01.parquet` snapshot and response-hash provenance.
- Made the PSX snapshot the primary classification evidence after explicit manual mappings.
- Restricted ticker regexes to historical symbols absent from the current PSX master.
- Retained exact rule/conflict traceability and the targeted review queue.

## Snapshot findings

- Master-backed classification intervals: 623.
- Historical ticker-fallback intervals: 76.
- Generic low-confidence `sector_prefix:08`: 87 intervals.
- Unknown intervals: 0.
- Competing-rule intervals: 769.
- Manual-review symbols: 785.

The master is a 2026-08-01 current-state snapshot. Any historical assignment based on it is labeled as a backcast, not contemporaneous PIT evidence.

The C5 negative linear conclusion is unchanged. No profitability analysis, nonlinear model, signal, portfolio, execution, or backtest is introduced.

## Verification

- Complete CPU-only suite with CUDA hidden: **60 passed, 1 expected GPU skip in 8.51 seconds**.
- Two consecutive master-first runs reproduced the logical hashes in `C6_MANIFEST.json`.
- Final holdout accessed: **false**.
- Production DB SHA-256: `e35f224284481ab00650d6f65e495f79318f7580f340ebd6bf23fd3f08aeb67b`.
- Watcher HEAD: `404e3637637ca89d4455b9f7069c6191a3658d83`; porcelain status empty.
