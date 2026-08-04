# C10 Transaction Cost Report

## Scope

Checkpoint 3 applies explicit transaction costs to the audited Checkpoint 2 frictionless trade and NAV ledgers.

Baseline actual broker schedule, derived from the user's real transaction ledger:

- commission: 0.15% of transaction value or PKR 0.03/share, whichever is higher;
- SST: 15% of commission;
- CDC: PKR 0.005/share;
- applied independently to buys and sells.

Sensitivity scenarios use 0.20% and 0.25% ad-valorem brokerage while retaining the PKR 0.03 per-share floor.

Configured but currently zero:

- additional notional levies;
- tax on brokerage;
- fixed per-trade fees.

Excluded:

- capital gains tax;
- slippage and bid/ask spread;
- market impact;
- capacity limits;
- board-lot restrictions;
- financing costs.

## Method

For each policy and cost scenario:

1. Calculate exact trade-level brokerage from shares and notional.
2. Aggregate costs by trade date.
3. Convert daily cost to a fraction of the prior gross closing NAV.
4. Deduct the cost fraction before applying that day's gross portfolio return.
5. Compound the resulting net daily return series.

This return-level overlay preserves the audited Checkpoint 2 gross holdings and execution decisions. It does not resize future holdings after costs.

## Results

| cost_schedule_id           | policy_id                 | start_date   | end_date   |   observations |   starting_capital |   ending_net_nav |   net_total_return |   net_annualized_return |   net_annualized_volatility |   net_sharpe_zero_rf |   net_max_drawdown |   total_transaction_cost |   total_brokerage |   total_sst |   total_cdc |   total_traded_notional |   weighted_average_cost_rate |   cost_days |   trade_count |   ending_gross_nav |   gross_total_return |   ending_nav_cost_drag |
|:---------------------------|:--------------------------|:-------------|:-----------|---------------:|-------------------:|-----------------:|-------------------:|------------------------:|----------------------------:|---------------------:|-------------------:|-------------------------:|------------------:|------------:|------------:|------------------------:|-----------------------------:|------------:|--------------:|-------------------:|---------------------:|-----------------------:|
| actual_broker_20bps        | P1_broad_canonical        | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      2.99393e+06 |            1.99393 |                0.442602 |                    0.18264  |              2.1344  |          -0.184801 |         992246           |  818253           |    122738   |     51255.2 |             3.64988e+08 |                   0.00271857 |         158 |          3866 |        4.81135e+06 |              3.81135 |            1.81743e+06 |
| actual_broker_20bps        | P2_conservative_consensus | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.13531e+06 |            2.13531 |                0.465018 |                    0.187335 |              2.16943 |          -0.181858 |         995637           |  825555           |    123833   |     46248.8 |             3.81597e+08 |                   0.00260913 |         158 |          3183 |        5.03056e+06 |              4.03056 |            1.89525e+06 |
| actual_broker_20bps        | P4_kmi30_strict           | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.13959e+06 |            2.13959 |                0.465687 |                    0.325705 |              1.35718 |          -0.269682 |              1.52165e+06 |       1.26278e+06 |    189416   |     69461.4 |             5.88698e+08 |                   0.00258478 |         157 |           738 |        5.06717e+06 |              4.06717 |            1.92758e+06 |
| actual_broker_25bps        | P1_broad_canonical        | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      2.74383e+06 |            1.74383 |                0.401157 |                    0.183141 |              1.96686 |          -0.193993 |              1.18614e+06 |  986855           |    148028   |     51255.2 |             3.64988e+08 |                   0.0032498  |         158 |          3866 |        4.81135e+06 |              3.81135 |            2.06752e+06 |
| actual_broker_25bps        | P2_conservative_consensus | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      2.85743e+06 |            1.85743 |                0.420282 |                    0.187875 |              1.99552 |          -0.192635 |              1.20101e+06 |       1.00414e+06 |    150621   |     46248.8 |             3.81597e+08 |                   0.00314734 |         158 |          3183 |        5.03056e+06 |              4.03056 |            2.17312e+06 |
| actual_broker_25bps        | P4_kmi30_strict           | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      2.85004e+06 |            1.85004 |                0.419052 |                    0.326014 |              1.25515 |          -0.274825 |              1.83817e+06 |       1.53801e+06 |    230702   |     69461.4 |             5.88698e+08 |                   0.00312244 |         157 |           738 |        5.06717e+06 |              4.06717 |            2.21713e+06 |
| actual_broker_all_in       | P1_broad_canonical        | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.25346e+06 |            2.25346 |                0.48324  |                    0.182247 |              2.29396 |          -0.176112 |         806886           |  657070           |     98560.5 |     51255.2 |             3.64988e+08 |                   0.00221072 |         158 |          3866 |        4.81135e+06 |              3.81135 |            1.5579e+06  |
| actual_broker_all_in       | P2_conservative_consensus | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.42985e+06 |            2.42985 |                0.509642 |                    0.186915 |              2.33749 |          -0.171291 |         795974           |  651935           |     97790.3 |     46248.8 |             3.81597e+08 |                   0.0020859  |         158 |          3183 |        5.03056e+06 |              4.03056 |            1.60071e+06 |
| actual_broker_all_in       | P4_kmi30_strict           | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.44595e+06 |            2.44595 |                0.512007 |                    0.325476 |              1.45532 |          -0.26458  |              1.21511e+06 |  996215           |    149432   |     69461.4 |             5.88698e+08 |                   0.00206406 |         157 |           738 |        5.06717e+06 |              4.06717 |            1.62121e+06 |
| psx_minimum_brokerage_only | P1_broad_canonical        | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.50791e+06 |            2.50791 |                0.521038 |                    0.181916 |              2.43879 |          -0.167015 |         657070           |  657070           |         0   |         0   |             3.64988e+08 |                   0.00180025 |         158 |          3866 |        4.81135e+06 |              3.81135 |            1.30344e+06 |
| psx_minimum_brokerage_only | P2_conservative_consensus | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.68613e+06 |            2.68613 |                0.546436 |                    0.186564 |              2.4731  |          -0.161305 |         651935           |  651935           |         0   |         0   |             3.81597e+08 |                   0.00170844 |         158 |          3183 |        5.03056e+06 |              4.03056 |            1.34443e+06 |
| psx_minimum_brokerage_only | P4_kmi30_strict           | 2023-01-03   | 2025-12-31 |            741 |              1e+06 |      3.69892e+06 |            2.69892 |                0.548227 |                    0.325318 |              1.53003 |          -0.261436 |         996215           |  996215           |         0   |         0   |             5.88698e+08 |                   0.00169223 |         157 |           738 |        5.06717e+06 |              4.06717 |            1.36825e+06 |

## Outputs

- Costed trades: `data/processed/c10/costed_trades.parquet`
- Costed daily NAV: `data/processed/c10/costed_nav.parquet`
- Cost summary: `data/processed/c10/cost_summary.parquet`
