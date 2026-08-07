# C11 CP2 — Whole-Share Capital-Aware Deployment Report

## Scope

This checkpoint measures the deployment cost of whole-share execution across the CP1-frozen capital grid.

Included:

- accepted C10 P1, P2, P4 and P5 selections;
- next-session `open_adj` execution;
- whole shares only;
- equal target weights;
- net-to-target rebalancing;
- exact `actual_broker_all_in` costs deducted from cash at each trade;
- explicit residual cash;
- no leverage;
- C10 missing-close and deferred-exit valuation rules.

Not yet included:

- P1/P2 Shariah filter/refill transformation;
- policy combinations;
- gap/limit-order rules;
- partial fills or intraday market impact;
- stop-loss logic.

**Important:** P1/P2 rows in CP2 are research diagnostics only. They are not final executable C11 portfolios until the mandatory Shariah gate is applied in the later deployment-policy checkpoint.

## Results

| policy_id                 |   starting_capital |       ending_nav |   annualized_return |   sharpe_zero_rf |   max_drawdown |   mean_cash_fraction |   total_skipped_price_targets |   rebalance_dates_with_price_skips |   total_transaction_cost |   annualized_return_delta_vs_c10_reference |
|:--------------------------|-------------------:|-----------------:|--------------------:|-----------------:|---------------:|---------------------:|------------------------------:|-----------------------------------:|-------------------------:|-------------------------------------------:|
| P1_broad_canonical        |          50000     | 157482           |            0.467251 |          2.27763 |      -0.174197 |          0.0452245   |                            56 |                                 49 |          30077.8         |                               -0.0159889   |
| P2_conservative_consensus |          50000     | 166628           |            0.495194 |          2.32429 |      -0.169093 |          0.0441778   |                            53 |                                 49 |          29787.8         |                               -0.0144486   |
| P4_kmi30_strict           |          50000     | 172443           |            0.512434 |          1.45757 |      -0.264221 |          0.00119622  |                             0 |                                  0 |          48054.7         |                                0.00042738  |
| P5_shariah_screened       |          50000     | 181004           |            0.53712  |          1.60379 |      -0.226333 |          0.00348639  |                             0 |                                  0 |          63381.4         |                                0.00130966  |
| P1_broad_canonical        |         100000     | 319402           |            0.474129 |          2.28261 |      -0.174799 |          0.0240908   |                            22 |                                 22 |          61683.6         |                               -0.00911103  |
| P2_conservative_consensus |         100000     | 336597           |            0.500188 |          2.3225  |      -0.170329 |          0.0236265   |                            20 |                                 20 |          60987.7         |                               -0.00945444  |
| P4_kmi30_strict           |         100000     | 345202           |            0.512895 |          1.45771 |      -0.264465 |          0.000513767 |                             0 |                                  0 |          96242.4         |                                0.000888507 |
| P5_shariah_screened       |         100000     | 362768           |            0.538198 |          1.60343 |      -0.227117 |          0.0012916   |                             0 |                                  0 |         127160           |                                0.00238811  |
| P1_broad_canonical        |         250000     | 811003           |            0.4818   |          2.29564 |      -0.175538 |          0.0085542   |                             1 |                                  1 |         156770           |                               -0.00144037  |
| P2_conservative_consensus |         250000     | 851047           |            0.505858 |          2.3309  |      -0.170863 |          0.00844027  |                             0 |                                  0 |         154846           |                               -0.00378451  |
| P4_kmi30_strict           |         250000     | 863355           |            0.513101 |          1.45772 |      -0.264416 |          0.000156766 |                             0 |                                  0 |         240700           |                                0.00109392  |
| P5_shariah_screened       |         250000     | 905795           |            0.53756  |          1.60081 |      -0.227852 |          0.000244437 |                             0 |                                  0 |         317693           |                                0.00174998  |
| P1_broad_canonical        |         500000     |      1.62403e+06 |            0.482418 |          2.29351 |      -0.175708 |          0.0044051   |                             0 |                                  0 |         314621           |                               -0.000821978 |
| P2_conservative_consensus |         500000     |      1.71147e+06 |            0.508624 |          2.33629 |      -0.170993 |          0.00389853  |                             0 |                                  0 |         311469           |                               -0.00101876  |
| P4_kmi30_strict           |         500000     |      1.72676e+06 |            0.513115 |          1.45767 |      -0.264438 |          7.09347e-05 |                             0 |                                  0 |         481426           |                                0.00110859  |
| P5_shariah_screened       |         500000     |      1.81123e+06 |            0.537459 |          1.60054 |      -0.228033 |          5.64579e-05 |                             0 |                                  0 |         635513           |                                0.0016488   |
| P1_broad_canonical        |              1e+06 |      3.25194e+06 |            0.483008 |          2.2937  |      -0.175859 |          0.0019858   |                             0 |                                  0 |         630711           |                               -0.000231822 |
| P2_conservative_consensus |              1e+06 |      3.43085e+06 |            0.509789 |          2.33852 |      -0.171133 |          0.0019855   |                             0 |                                  0 |         624299           |                                0.000146844 |
| P4_kmi30_strict           |              1e+06 |      3.45378e+06 |            0.513154 |          1.45772 |      -0.26445  |          3.49152e-05 |                             0 |                                  0 |         962915           |                                0.00114726  |
| P5_shariah_screened       |              1e+06 |      3.62119e+06 |            0.537279 |          1.60009 |      -0.228104 |          1.61374e-05 |                             0 |                                  0 |              1.27077e+06 |                                0.00146836  |

## C10 reference comparison

`annualized_return_delta_vs_c10_reference` compares the C11 whole-share, exact-cash result against the accepted C10 fractional-share `actual_broker_all_in` annualized return.

**This is a reference/reconciliation metric, not a pure whole-share drag measurement.** C10 applies transaction costs as a return-level overlay on the gross portfolio ledger, while C11 CP2 deducts exact transaction costs directly from portfolio cash at each trade. The two systems therefore differ in both share granularity and fee-accounting mechanics. A positive or negative delta must not be interpreted as the isolated effect of whole-share sizing.

C10 remains immutable.

## Outputs

- `data/processed/c11/whole_share_trades.parquet`
- `data/processed/c11/whole_share_positions.parquet`
- `data/processed/c11/whole_share_nav.parquet`
- `data/processed/c11/whole_share_summary.parquet`
