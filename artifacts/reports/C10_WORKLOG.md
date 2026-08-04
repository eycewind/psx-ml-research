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

## Checkpoint 4 — Liquidity and capacity diagnostics

- Used point-in-time `turnover_median_20obs_adj`.
- Liquidity was joined using the latest valid observation on or before each signal date.
- No execution-day or future turnover was used.
- Exact-date liquidity matches:
  - P1: 3,861 of 3,866 trades
  - P2: 3,180 of 3,183 trades
- All remaining observations used a prior value no more than 3 calendar days old.
- Missing liquidity rows after as-of fallback: 0.
- Tested participation caps of 5%, 10% and 20%.
- Tested capital levels of PKR 1m, 5m, 10m, 25m and 50m.
- At PKR 1m and 10% participation:
  - P1 fully feasible trades: 90.87%
  - P1 notional fill: 94.63%
  - P2 fully feasible trades: 87.21%
  - P2 notional fill: 92.38%
- P2 remained less scalable than P1.
- Capacity degradation became material at PKR 5m and severe at PKR 10m.
- This checkpoint remained diagnostic only; partial fills were not fed into holdings or NAV.
- No 2026 holdout data was accessed.

## CP4A — P4 strict KMI-30 integration

- Added `P4_kmi30_strict`.
- Used point-in-time KMI-30 membership from six official PSX recomposition intervals.
- Generated 471 selections over 157 weekly dates.
- Selected exactly three holdings per signal date.
- Every selected row was an effective KMI-30 member.
- P4 entry availability was 100%.
- Integrated P4 into Checkpoints 1–4.
- Existing P1/P2 frictionless ledgers remained unchanged.

### Frictionless P4

- Ending NAV: PKR 5.067m
- Annualized return: 71.99%
- Annualized volatility: 32.51%
- Sharpe: 1.86
- Maximum drawdown: -24.66%

### Actual all-in costs

- Ending net NAV: PKR 3.446m
- Annualized net return: 51.20%
- Net Sharpe: 1.46
- Net maximum drawdown: -26.46%
- Weighted average all-in transaction cost: 0.2064%

### Capacity

At PKR 1m and 10% participation:

- Fully feasible trades: 98.10%
- Notional fill: 99.39%

At PKR 5m and 10% participation:

- Fully feasible trades: 79.54%
- Notional fill: 86.97%

At PKR 10m and 10% participation:

- Fully feasible trades: 70.33%
- Notional fill: 76.82%

P4 was materially more scalable than P1/P2 but had substantially higher concentration risk, volatility and drawdown.
