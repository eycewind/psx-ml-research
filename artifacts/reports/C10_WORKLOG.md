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

## Checkpoint 2 — Frictionless portfolio engine

- Built independent P1 and P2 equal-weight portfolios.
- Starting capital: PKR 1,000,000 per policy.
- Entry execution: next-session adjusted open.
- Valuation: daily adjusted close.
- Missing closes: latest prior valid close, without lookahead.
- Blocked exits: first later valid adjusted open.
- Deferred-exit proceeds remain cash until the next scheduled rebalance.
- Fractional shares are permitted.
- No fees, taxes, slippage, board lots or capacity restrictions.
- Ledger reconciliation and temporal audits passed.

## Checkpoint 3 — Transaction-cost model

- Applied transaction costs to the audited Checkpoint 2 gross ledger.
- Primary baseline calibrated from actual broker transaction records:
  - commission: max(0.15% of notional, PKR 0.03/share)
  - SST: 15% of commission
  - CDC: PKR 0.005/share
- The adjustment transaction was excluded from cost calibration.
- Retained a commission-only regulatory-minimum comparison.
- Added 0.20% and 0.25% commission sensitivity scenarios with SST and CDC.
- Applied costs independently to buys and sells.
- Baseline weighted all-in cost:
  - P1: 0.2211%
  - P2: 0.2086%
- Baseline net annualized return:
  - P1: 48.32%
  - P2: 50.96%
- Baseline net maximum drawdown:
  - P1: -17.61%
  - P2: -17.13%
- P2 remained stronger than P1 after transaction costs.
- No 2026 holdout data was used.
- CGT, slippage, spread, impact, capacity, board lots and financing remain excluded.
