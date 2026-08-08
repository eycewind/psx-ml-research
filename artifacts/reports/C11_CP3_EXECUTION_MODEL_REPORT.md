# C11 CP3 — One-Session Limit Execution Model

## Frozen execution rule

Primary deployment proxy:

- BUY reference: signal-session `close_adj`;
- BUY maximum price: signal close + 2%;
- validity: next trading session only;
- if next-session open <= limit: fill at open;
- otherwise, if next-session low <= limit: fill at limit and mark `intraday_touch_proxy`;
- otherwise: BUY addition is missed and is not chased on a later day;
- SELL reductions and exits: next available open, retaining the accepted deferred-exit rule;
- whole shares only;
- exact `actual_broker_all_in` costs deducted from cash;
- no leverage.

The `intraday_touch_proxy` is not claimed to be a certain fill. Daily OHLC proves only that the level was touched during the session; it does not establish queue priority or intraday sequencing.

`buy_fill_fraction` counts only BUY additions that actually execute at least one whole share. If the price rule is satisfied but available cash cannot fund one whole share after exact fees, the attempt is recorded separately as `unfunded_buy_additions` and is not counted as a fill.

Conservative sensitivity:

- `open_only`: a BUY fills only when the next-session open is at/below the limit.

Premium sensitivities of +1% and +3% are reported only as robustness scenarios. They are **not** candidates from which C11 selects the historically best-performing threshold.

P1/P2 remain research diagnostics at CP3. They cannot become executable C11 portfolios until the mandatory PIT Shariah gate is applied.

## Primary +2% touch-fill results

| policy_id                 |   starting_capital |       ending_nav |   annualized_return |   sharpe_zero_rf |   max_drawdown |   buy_fill_fraction |   missed_buy_additions |   unfunded_buy_additions |   mean_cash_fraction |   annualized_return_delta_vs_cp2 |
|:--------------------------|-------------------:|-----------------:|--------------------:|-----------------:|---------------:|--------------------:|-----------------------:|-------------------------:|---------------------:|---------------------------------:|
| P1_broad_canonical        |          50000     | 153400           |            0.45443  |          2.27483 |      -0.169792 |            0.986711 |                     24 |                        0 |           0.054328   |                      -0.0128206  |
| P2_conservative_consensus |          50000     | 161896           |            0.48087  |          2.31782 |      -0.166889 |            0.984687 |                     23 |                        0 |           0.0547012  |                      -0.0143241  |
| P4_kmi30_strict           |          50000     | 173053           |            0.514218 |          1.4691  |      -0.264026 |            0.986702 |                      5 |                        0 |           0.00803039 |                       0.00178414 |
| P5_shariah_screened       |          50000     | 178931           |            0.531215 |          1.62585 |      -0.216557 |            0.972625 |                     32 |                        2 |           0.0196575  |                      -0.00590527 |
| P1_broad_canonical        |         100000     | 311661           |            0.462093 |          2.28232 |      -0.170225 |            0.987281 |                     24 |                        0 |           0.0330713  |                      -0.0120362  |
| P2_conservative_consensus |         100000     | 327684           |            0.486793 |          2.31897 |      -0.168951 |            0.98536  |                     23 |                        0 |           0.0352653  |                      -0.0133947  |
| P4_kmi30_strict           |         100000     | 346046           |            0.514131 |          1.46776 |      -0.264293 |            0.986807 |                      5 |                        0 |           0.00725008 |                       0.00123543 |
| P5_shariah_screened       |         100000     | 358027           |            0.531451 |          1.62331 |      -0.216973 |            0.973642 |                     32 |                        1 |           0.0173965  |                      -0.00674737 |
| P1_broad_canonical        |         250000     | 793106           |            0.470791 |          2.29986 |      -0.171023 |            0.986674 |                     25 |                        1 |           0.0180269  |                      -0.011009   |
| P2_conservative_consensus |         250000     | 830003           |            0.493311 |          2.32887 |      -0.169171 |            0.985267 |                     24 |                        0 |           0.0201342  |                      -0.0125467  |
| P4_kmi30_strict           |         250000     | 865800           |            0.514532 |          1.46826 |      -0.264442 |            0.986807 |                      5 |                        0 |           0.00695307 |                       0.00143091 |
| P5_shariah_screened       |         250000     | 895879           |            0.531915 |          1.62303 |      -0.217541 |            0.972222 |                     32 |                        3 |           0.0163875  |                      -0.00564521 |
| P1_broad_canonical        |         500000     |      1.5883e+06  |            0.471438 |          2.29765 |      -0.171311 |            0.986862 |                     26 |                        0 |           0.013868   |                      -0.01098    |
| P2_conservative_consensus |         500000     |      1.6702e+06  |            0.49637  |          2.33623 |      -0.169372 |            0.98541  |                     24 |                        0 |           0.0152824  |                      -0.0122539  |
| P4_kmi30_strict           |         500000     |      1.732e+06   |            0.514647 |          1.46844 |      -0.264456 |            0.986807 |                      5 |                        0 |           0.00687132 |                       0.001532   |
| P5_shariah_screened       |         500000     |      1.79271e+06 |            0.532187 |          1.62331 |      -0.217535 |            0.97231  |                     32 |                        3 |           0.0160906  |                      -0.00527203 |
| P1_broad_canonical        |              1e+06 |      3.18477e+06 |            0.472702 |          2.30022 |      -0.171319 |            0.985965 |                     26 |                        2 |           0.0116464  |                      -0.0103065  |
| P2_conservative_consensus |              1e+06 |      3.34716e+06 |            0.497381 |          2.33742 |      -0.16942  |            0.985525 |                     24 |                        0 |           0.0132678  |                      -0.0124082  |
| P4_kmi30_strict           |              1e+06 |      3.46418e+06 |            0.514675 |          1.46847 |      -0.264451 |            0.986807 |                      5 |                        0 |           0.00682557 |                       0.00152132 |
| P5_shariah_screened       |              1e+06 |      3.58467e+06 |            0.53208  |          1.62292 |      -0.217578 |            0.972376 |                     32 |                        3 |           0.0159927  |                      -0.0051986  |

## Sensitivity at PKR 1,000,000

| scenario_id        | policy_id                 |   annualized_return |   sharpe_zero_rf |   max_drawdown |   buy_fill_fraction |   missed_buy_additions |   unfunded_buy_additions |   mean_cash_fraction |
|:-------------------|:--------------------------|--------------------:|-----------------:|---------------:|--------------------:|-----------------------:|-------------------------:|---------------------:|
| open_only_1pct     | P1_broad_canonical        |            0.450671 |          2.57413 |      -0.137932 |            0.834473 |                    339 |                        0 |           0.111561   |
| open_only_2pct     | P1_broad_canonical        |            0.460459 |          2.40809 |      -0.171666 |            0.940209 |                    120 |                        0 |           0.0419469  |
| open_only_3pct     | P1_broad_canonical        |            0.450385 |          2.26888 |      -0.173737 |            0.972431 |                     54 |                        1 |           0.0207548  |
| touch_1pct         | P1_broad_canonical        |            0.497078 |          2.41169 |      -0.164539 |            0.977023 |                     46 |                        0 |           0.0185971  |
| touch_2pct_primary | P1_broad_canonical        |            0.472702 |          2.30022 |      -0.171319 |            0.985965 |                     26 |                        2 |           0.0116464  |
| touch_3pct         | P1_broad_canonical        |            0.468848 |          2.26696 |      -0.174657 |            0.991964 |                     14 |                        2 |           0.00788015 |
| open_only_1pct     | P2_conservative_consensus |            0.424841 |          2.40553 |      -0.13275  |            0.838253 |                    274 |                        0 |           0.111182   |
| open_only_2pct     | P2_conservative_consensus |            0.47638  |          2.43199 |      -0.160899 |            0.942977 |                     95 |                        0 |           0.0421671  |
| open_only_3pct     | P2_conservative_consensus |            0.467559 |          2.29312 |      -0.171103 |            0.971014 |                     48 |                        0 |           0.0227431  |
| touch_1pct         | P2_conservative_consensus |            0.515211 |          2.42194 |      -0.16535  |            0.97586  |                     40 |                        0 |           0.0206983  |
| touch_2pct_primary | P2_conservative_consensus |            0.497381 |          2.33742 |      -0.16942  |            0.985525 |                     24 |                        0 |           0.0132678  |
| touch_3pct         | P2_conservative_consensus |            0.48748  |          2.2919  |      -0.171103 |            0.990931 |                     15 |                        0 |           0.00935733 |
| open_only_1pct     | P4_kmi30_strict           |            0.480543 |          1.49874 |      -0.262181 |            0.854545 |                     56 |                        0 |           0.101589   |
| open_only_2pct     | P4_kmi30_strict           |            0.474203 |          1.40962 |      -0.264456 |            0.957895 |                     16 |                        0 |           0.0243347  |
| open_only_3pct     | P4_kmi30_strict           |            0.515587 |          1.48395 |      -0.26445  |            0.978892 |                      8 |                        0 |           0.0128997  |
| touch_1pct         | P4_kmi30_strict           |            0.47359  |          1.39764 |      -0.266697 |            0.973684 |                     10 |                        0 |           0.0160816  |
| touch_2pct_primary | P4_kmi30_strict           |            0.514675 |          1.46847 |      -0.264451 |            0.986807 |                      5 |                        0 |           0.00682557 |
| touch_3pct         | P4_kmi30_strict           |            0.523627 |          1.48103 |      -0.26445  |            0.992063 |                      3 |                        0 |           0.0047745  |
| open_only_1pct     | P5_shariah_screened       |            0.588789 |          1.93829 |      -0.192433 |            0.760401 |                    310 |                        1 |           0.163548   |
| open_only_2pct     | P5_shariah_screened       |            0.498958 |          1.59949 |      -0.186234 |            0.902821 |                    121 |                        3 |           0.0631272  |
| open_only_3pct     | P5_shariah_screened       |            0.494897 |          1.55867 |      -0.212474 |            0.94633  |                     67 |                        1 |           0.037322   |
| touch_1pct         | P5_shariah_screened       |            0.557868 |          1.68971 |      -0.199352 |            0.959023 |                     49 |                        3 |           0.0248391  |
| touch_2pct_primary | P5_shariah_screened       |            0.53208  |          1.62292 |      -0.217578 |            0.972376 |                     32 |                        3 |           0.0159927  |
| touch_3pct         | P5_shariah_screened       |            0.528191 |          1.60417 |      -0.22401  |            0.979495 |                     22 |                        4 |           0.0119987  |

## CP2 comparison

`annualized_return_delta_vs_cp2` is a direct execution-model comparison because CP3 retains CP2's whole-share sizing, fee accounting, valuation rules and capital grid while adding the one-session BUY price cap/fill rule.

A CP3 improvement versus CP2 can arise from obtaining a lower assumed BUY price on `intraday_touch_proxy` rows. Such improvement must be interpreted cautiously because daily OHLC cannot prove that the full order would have filled at the limit.

## Outputs

- `data/processed/c11/execution_trades.parquet`
- `data/processed/c11/execution_positions.parquet`
- `data/processed/c11/execution_nav.parquet`
- `data/processed/c11/execution_summary.parquet`
