# C11 CP4B — Capital Allocation and Merged-Portfolio Execution

## Frozen evaluation design

CP4B does not search continuous allocation weights and does not select weights
by maximizing historical return.

The allocation grid was specified before this execution comparison:

- six standalones;
- P4/P5 at 25/75, 50/50 and 75/25;
- P2-filter/P5 at 25/75, 50/50 and 75/25;
- P2-refill/P5 at 25/75, 50/50 and 75/25;
- equal-third P2-filter/P4/P5;
- equal-third P2-refill/P4/P5.

P1 filter/refill remain standalone diagnostics because CP4A showed that P1
requires a large selection transformation under the Shariah gate.

## Portfolio construction

Each sleeve is equal-weight internally on each signal date. Sleeve weights are
then applied. If multiple sleeves select the same symbol, their weights are
aggregated into **one target position and one order stream**. NAVs from
independent sleeves are not added together.

Execution is the frozen CP3 primary rule:

- signal-session close +2% BUY limit;
- next session only;
- open fill when open <= limit;
- otherwise intraday-touch proxy at the limit when low <= limit;
- otherwise miss with no chase;
- whole shares;
- exact broker costs;
- no leverage;
- next-open reductions/exits with deferred exits where required.

## Target diagnostics

| policy_id           |   dates |   target_rows |   symbols |   target_count_min |   target_count_median |   target_count_max |   mean_max_target_weight |   max_target_weight |   mean_overlap_symbol_count |   max_overlap_symbol_count |
|:--------------------|--------:|--------------:|----------:|-------------------:|----------------------:|-------------------:|-------------------------:|--------------------:|----------------------------:|---------------------------:|
| A01_P1_filter       |     157 |          1470 |       166 |                  4 |                     9 |                 22 |                0.115919  |            0.25     |                    0        |                          0 |
| A02_P1_refill       |     157 |          2576 |       190 |                  9 |                    16 |                 27 |                0.0640812 |            0.111111 |                    0        |                          0 |
| A03_P2_filter       |     157 |          1173 |       153 |                  1 |                     7 |                 19 |                0.159873  |            1        |                    0        |                          0 |
| A04_P2_refill       |     157 |          1292 |       162 |                  1 |                     8 |                 20 |                0.146426  |            1        |                    0        |                          0 |
| A05_P4              |     157 |           471 |        51 |                  3 |                     3 |                  3 |                0.333333  |            0.333333 |                    0        |                          0 |
| A06_P5              |     157 |          1550 |       173 |                  7 |                    10 |                 15 |                0.106506  |            0.142857 |                    0        |                          0 |
| A07_P4_25_P5_75     |     157 |          1788 |       174 |                  7 |                    11 |                 17 |                0.146319  |            0.190476 |                    1.48408  |                          3 |
| A08_P4_50_P5_50     |     157 |          1788 |       174 |                  7 |                    11 |                 17 |                0.208164  |            0.238095 |                    1.48408  |                          3 |
| A09_P4_75_P5_25     |     157 |          1788 |       174 |                  7 |                    11 |                 17 |                0.270749  |            0.285714 |                    1.48408  |                          3 |
| A10_P2F_25_P5_75    |     157 |          2615 |       202 |                  8 |                    16 |                 32 |                0.0945372 |            0.25     |                    0.687898 |                          8 |
| A11_P2F_50_P5_50    |     157 |          2615 |       202 |                  8 |                    16 |                 32 |                0.0990759 |            0.5      |                    0.687898 |                          8 |
| A12_P2F_75_P5_25    |     157 |          2615 |       202 |                  8 |                    16 |                 32 |                0.129147  |            0.75     |                    0.687898 |                          8 |
| A13_P2R_25_P5_75    |     157 |          2726 |       203 |                  8 |                    16 |                 32 |                0.0931657 |            0.25     |                    0.738854 |                          8 |
| A14_P2R_50_P5_50    |     157 |          2726 |       203 |                  8 |                    16 |                 32 |                0.0927641 |            0.5      |                    0.738854 |                          8 |
| A15_P2R_75_P5_25    |     157 |          2726 |       203 |                  8 |                    16 |                 32 |                0.119222  |            0.75     |                    0.738854 |                          8 |
| A16_P2F_P4_P5_equal |     157 |          2835 |       203 |                  9 |                    17 |                 33 |                0.148082  |            0.333333 |                    2.16561  |                          8 |
| A17_P2R_P4_P5_equal |     157 |          2943 |       204 |                  9 |                    18 |                 34 |                0.147196  |            0.333333 |                    2.2293   |                          8 |

## PKR 1,000,000 results

| allocation_id       | allocation_category   |   ending_nav |   annualized_return |   annualized_volatility |   sharpe_zero_rf |   max_drawdown |   buy_fill_fraction |   missed_buy_additions |   unfunded_buy_additions |   mean_cash_fraction |   total_transaction_cost |
|:--------------------|:----------------------|-------------:|--------------------:|------------------------:|-----------------:|---------------:|--------------------:|-----------------------:|-------------------------:|---------------------:|-------------------------:|
| A01_P1_filter       | standalone_diagnostic |  2.31009e+06 |            0.322863 |                0.202045 |          1.51066 |      -0.233998 |            0.983696 |                     17 |                        1 |           0.0124231  |         510845           |
| A02_P1_refill       | standalone_diagnostic |  3.06764e+06 |            0.454375 |                0.19244  |          2.07821 |      -0.144299 |            0.987891 |                     24 |                        0 |           0.0114035  |         561669           |
| A03_P2_filter       | standalone            |  1.89451e+06 |            0.238031 |                0.211071 |          1.13509 |      -0.31924  |            0.981962 |                     16 |                        0 |           0.0141955  |         429123           |
| A04_P2_refill       | standalone            |  1.99273e+06 |            0.25912  |                0.206412 |          1.23939 |      -0.331044 |            0.983051 |                     16 |                        0 |           0.0141278  |         428799           |
| A05_P4              | standalone            |  3.46418e+06 |            0.514675 |                0.323321 |          1.46847 |      -0.264451 |            0.986807 |                      5 |                        0 |           0.00682557 |         960115           |
| A06_P5              | standalone            |  3.58467e+06 |            0.53208  |                0.294372 |          1.62292 |      -0.217578 |            0.972376 |                     32 |                        3 |           0.0159927  |              1.26298e+06 |
| A07_P4_25_P5_75     | two_policy            |  3.61632e+06 |            0.536587 |                0.287336 |          1.66592 |      -0.209292 |            0.975912 |                     33 |                        2 |           0.0136501  |              1.20425e+06 |
| A08_P4_50_P5_50     | two_policy            |  3.60361e+06 |            0.534781 |                0.290149 |          1.64828 |      -0.220823 |            0.973865 |                     34 |                        4 |           0.0113223  |              1.13434e+06 |
| A09_P4_75_P5_25     | two_policy            |  3.55468e+06 |            0.527785 |                0.302568 |          1.57714 |      -0.242057 |            0.972509 |                     33 |                        7 |           0.00900588 |              1.05251e+06 |
| A10_P2F_25_P5_75    | two_policy            |  3.14972e+06 |            0.467264 |                0.257226 |          1.64633 |      -0.196107 |            0.979228 |                     40 |                        2 |           0.0158203  |         984129           |
| A11_P2F_50_P5_50    | two_policy            |  2.71301e+06 |            0.395878 |                0.228641 |          1.59954 |      -0.196821 |            0.979892 |                     40 |                        1 |           0.0152336  |         754044           |
| A12_P2F_75_P5_25    | two_policy            |  2.28754e+06 |            0.318533 |                0.21228  |          1.43219 |      -0.257228 |            0.978911 |                     40 |                        3 |           0.0147155  |         572256           |
| A13_P2R_25_P5_75    | two_policy            |  3.188e+06   |            0.473201 |                0.256891 |          1.66415 |      -0.196409 |            0.980116 |                     40 |                        1 |           0.0160193  |         987817           |
| A14_P2R_50_P5_50    | two_policy            |  2.78074e+06 |            0.407427 |                0.227405 |          1.64391 |      -0.202317 |            0.980307 |                     40 |                        1 |           0.015199   |         756914           |
| A15_P2R_75_P5_25    | two_policy            |  2.3733e+06  |            0.33485  |                0.209533 |          1.50802 |      -0.266954 |            0.979827 |                     40 |                        2 |           0.0145631  |         574076           |
| A16_P2F_P4_P5_equal | three_policy          |  3.00932e+06 |            0.445075 |                0.244329 |          1.65634 |      -0.178877 |            0.980935 |                     41 |                        1 |           0.0125978  |         823343           |
| A17_P2R_P4_P5_equal | three_policy          |  3.05971e+06 |            0.453118 |                0.243814 |          1.68251 |      -0.17679  |            0.981342 |                     41 |                        1 |           0.0126636  |         825789           |

## Decision boundary

These results are diagnostic. CP4B must not choose the historically highest
returning allocation mechanically. The final deployment choice should consider
risk-adjusted return, drawdown, cash drag, execution quality, concentration,
overlap and the provenance/degree of transformation of each input policy.
Concentration and overlap are investigated explicitly in CP5.

## Outputs

- `data/processed/c11/cp4b_allocation_targets.parquet`
- `data/processed/c11/cp4b_execution_trades.parquet`
- `data/processed/c11/cp4b_execution_positions.parquet`
- `data/processed/c11/cp4b_execution_nav.parquet`
- `data/processed/c11/cp4b_allocation_summary.parquet`
