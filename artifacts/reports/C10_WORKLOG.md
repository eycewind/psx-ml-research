# C10 Worklog

## Contract initialization

- Branch: `feature/c10-fee-aware-portfolio-backtest`
- Objective: Start C10 fee-aware portfolio and execution backtest.
- Frozen policies:
  - `P1_broad_canonical`
  - `P2_conservative_consensus`
- Final 2026 holdout: locked
- Status: contract added; implementation not started.

## Checkpoint 1 — Input and price audit

- Authoritative selection input:
  `data/processed/c9/candidate_selections.parquet`
- Frozen policies retained:
  `P1_broad_canonical` and `P2_conservative_consensus`
- Other C9 policies are ignored.
- Execution-price source:
  `data/cache/daily_ohlcv.parquet`
- Canonical entry:
  next-session `open_adj`
- Canonical valuation:
  `close_adj`
- Prices may extend past the last signal date through 2025-12-31.
- All 2026 rows remain blocked.
- Entry availability:
  P1 2576/2576, P2 2120/2120.
- No missing next-session entries.
- Portfolio accounting and costs remain out of scope for Checkpoint 1.
