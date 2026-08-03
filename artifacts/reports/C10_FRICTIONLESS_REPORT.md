# C10 Frictionless Portfolio Report

## Scope

This checkpoint evaluates portfolio construction and gross accounting only.

Included:

- frozen C9 policies P1 and P2;
- next-session adjusted-open execution;
- equal target weights at every weekly rebalance;
- net trading from existing holdings to new target holdings;
- fractional shares;
- daily adjusted-close valuation;
- prior-close carry-forward for missing daily closes;
- deferred exits when an outgoing holding has no valid rebalance-date open;
- explicit cash and invested-value accounting.

Excluded:

- brokerage;
- taxes and levies;
- slippage;
- bid/ask spread;
- market impact;
- board-lot restrictions;
- capacity limits;
- financing and interest.

Starting capital for each independent policy portfolio: PKR 1,000,000.00

## Gross performance

| policy_id                 | start_date   | end_date   |   observations |   starting_capital |   ending_nav |   total_return |   annualized_return |   annualized_volatility |   sharpe_zero_rf |   max_drawdown |   positive_day_fraction |   rebalance_count |   stale_position_days |   pending_exit_days |   max_pending_exits |   trade_rows |   position_rows |   unique_symbols_traded |   deferred_exit_trades |
|:--------------------------|:-------------|:-----------|---------------:|-------------------:|-------------:|---------------:|--------------------:|------------------------:|-----------------:|---------------:|------------------------:|------------------:|----------------------:|--------------------:|--------------------:|-------------:|----------------:|------------------------:|-----------------------:|
| P1_broad_canonical        | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |  4.81135e+06 |        3.81135 |            0.69042  |                0.181359 |          3.03928 |      -0.136825 |                0.605938 |               157 |                    18 |                   1 |                   1 |         3866 |           12198 |                     249 |                      1 |
| P2_conservative_consensus | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |  5.03056e+06 |        4.03056 |            0.715776 |                0.185833 |          3.05219 |      -0.129172 |                0.59919  |               157 |                    15 |                   1 |                   1 |         3183 |           10037 |                     231 |                      1 |

## Output ledgers

- Trades: `data/processed/c10/frictionless_trades.parquet`
- Positions: `data/processed/c10/frictionless_positions.parquet`
- Daily NAV: `data/processed/c10/frictionless_nav.parquet`

These are frictionless results and are not estimates of realizable net performance.
