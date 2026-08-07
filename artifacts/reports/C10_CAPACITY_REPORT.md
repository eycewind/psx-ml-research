# C10 Liquidity and Capacity Report

## Scope

Checkpoint 4 measures whether the frozen P1, P2, P4 and P5 trade ledgers can be executed at larger portfolio sizes.

Capacity reference:

- `turnover_median_20obs_adj`
- joined using each trade's `signal_date`
- no execution-day or future turnover is used

Participation scenarios:

- 5% of reference turnover
- 10% of reference turnover
- 20% of reference turnover

Portfolio capital scenarios:

- PKR 1 million
- PKR 5 million
- PKR 10 million
- PKR 25 million
- PKR 50 million

Missing or non-positive liquidity is treated as zero executable capacity.

## Method

For each trade:

1. Scale the Checkpoint 2 trade notional by portfolio capital.
2. Compute capacity as point-in-time median turnover multiplied by the participation cap.
3. Compute the maximum executable notional and fill ratio.
4. Record full feasibility, capacity breach and unfilled notional.

This checkpoint is diagnostic only. It does not yet feed partial fills back into holdings, cash or NAV.

## Scenario summary

| scenario_id                          | policy_id                 |   portfolio_capital |   participation_rate |   fully_feasible_fraction |   notional_fill_fraction |   capacity_breach_trades |   breach_date_count |
|:-------------------------------------|:--------------------------|--------------------:|---------------------:|--------------------------:|-------------------------:|-------------------------:|--------------------:|
| capital_10000000_participation_10pct | P1_broad_canonical        |             1e+07   |                 0.1  |                  0.512675 |                 0.545234 |                     1884 |                 158 |
| capital_10000000_participation_10pct | P2_conservative_consensus |             1e+07   |                 0.1  |                  0.455859 |                 0.488055 |                     1732 |                 158 |
| capital_10000000_participation_10pct | P4_kmi30_strict           |             1e+07   |                 0.1  |                  0.703252 |                 0.76818  |                      219 |                 108 |
| capital_10000000_participation_10pct | P5_shariah_screened       |             1e+07   |                 0.1  |                  0.55839  |                 0.639728 |                     1108 |                 141 |
| capital_10000000_participation_20pct | P1_broad_canonical        |             1e+07   |                 0.2  |                  0.629591 |                 0.688703 |                     1432 |                 158 |
| capital_10000000_participation_20pct | P2_conservative_consensus |             1e+07   |                 0.2  |                  0.566761 |                 0.633262 |                     1379 |                 158 |
| capital_10000000_participation_20pct | P4_kmi30_strict           |             1e+07   |                 0.2  |                  0.795393 |                 0.869699 |                      151 |                  92 |
| capital_10000000_participation_20pct | P5_shariah_screened       |             1e+07   |                 0.2  |                  0.683141 |                 0.794979 |                      795 |                 129 |
| capital_10000000_participation_5pct  | P1_broad_canonical        |             1e+07   |                 0.05 |                  0.403777 |                 0.417096 |                     2305 |                 158 |
| capital_10000000_participation_5pct  | P2_conservative_consensus |             1e+07   |                 0.05 |                  0.35721  |                 0.366019 |                     2046 |                 158 |
| capital_10000000_participation_5pct  | P4_kmi30_strict           |             1e+07   |                 0.05 |                  0.565041 |                 0.634479 |                      321 |                 123 |
| capital_10000000_participation_5pct  | P5_shariah_screened       |             1e+07   |                 0.05 |                  0.46393  |                 0.500781 |                     1345 |                 147 |
| capital_1000000_participation_10pct  | P1_broad_canonical        |             1e+06   |                 0.1  |                  0.908691 |                 0.946349 |                      353 |                 127 |
| capital_1000000_participation_10pct  | P2_conservative_consensus |             1e+06   |                 0.1  |                  0.872133 |                 0.923763 |                      407 |                 135 |
| capital_1000000_participation_10pct  | P4_kmi30_strict           |             1e+06   |                 0.1  |                  0.98103  |                 0.993869 |                       14 |                  14 |
| capital_1000000_participation_10pct  | P5_shariah_screened       |             1e+06   |                 0.1  |                  0.978477 |                 0.992581 |                       54 |                  22 |
| capital_1000000_participation_20pct  | P1_broad_canonical        |             1e+06   |                 0.2  |                  0.973099 |                 0.98653  |                      104 |                  65 |
| capital_1000000_participation_20pct  | P2_conservative_consensus |             1e+06   |                 0.2  |                  0.957901 |                 0.977921 |                      134 |                  79 |
| capital_1000000_participation_20pct  | P4_kmi30_strict           |             1e+06   |                 0.2  |                  0.99458  |                 0.998648 |                        4 |                   4 |
| capital_1000000_participation_20pct  | P5_shariah_screened       |             1e+06   |                 0.2  |                  0.999203 |                 0.999591 |                        2 |                   2 |
| capital_1000000_participation_5pct   | P1_broad_canonical        |             1e+06   |                 0.05 |                  0.797724 |                 0.857926 |                      782 |                 152 |
| capital_1000000_participation_5pct   | P2_conservative_consensus |             1e+06   |                 0.05 |                  0.744581 |                 0.820167 |                      813 |                 156 |
| capital_1000000_participation_5pct   | P4_kmi30_strict           |             1e+06   |                 0.05 |                  0.920054 |                 0.963406 |                       59 |                  45 |
| capital_1000000_participation_5pct   | P5_shariah_screened       |             1e+06   |                 0.05 |                  0.895177 |                 0.952456 |                      263 |                  85 |
| capital_25000000_participation_10pct | P1_broad_canonical        |             2.5e+07 |                 0.1  |                  0.372219 |                 0.379714 |                     2427 |                 158 |
| capital_25000000_participation_10pct | P2_conservative_consensus |             2.5e+07 |                 0.1  |                  0.328307 |                 0.331981 |                     2138 |                 158 |
| capital_25000000_participation_10pct | P4_kmi30_strict           |             2.5e+07 |                 0.1  |                  0.517615 |                 0.583718 |                      356 |                 128 |
| capital_25000000_participation_10pct | P5_shariah_screened       |             2.5e+07 |                 0.1  |                  0.432842 |                 0.459749 |                     1423 |                 149 |
| capital_25000000_participation_20pct | P1_broad_canonical        |             2.5e+07 |                 0.2  |                  0.480859 |                 0.502279 |                     2007 |                 158 |
| capital_25000000_participation_20pct | P2_conservative_consensus |             2.5e+07 |                 0.2  |                  0.422872 |                 0.446229 |                     1837 |                 158 |
| capital_25000000_participation_20pct | P4_kmi30_strict           |             2.5e+07 |                 0.2  |                  0.658537 |                 0.72891  |                      252 |                 113 |
| capital_25000000_participation_20pct | P5_shariah_screened       |             2.5e+07 |                 0.2  |                  0.528099 |                 0.593003 |                     1184 |                 144 |
| capital_25000000_participation_5pct  | P1_broad_canonical        |             2.5e+07 |                 0.05 |                  0.275737 |                 0.27617  |                     2800 |                 158 |
| capital_25000000_participation_5pct  | P2_conservative_consensus |             2.5e+07 |                 0.05 |                  0.241596 |                 0.240396 |                     2414 |                 158 |
| capital_25000000_participation_5pct  | P4_kmi30_strict           |             2.5e+07 |                 0.05 |                  0.375339 |                 0.404829 |                      461 |                 135 |
| capital_25000000_participation_5pct  | P5_shariah_screened       |             2.5e+07 |                 0.05 |                  0.350737 |                 0.344467 |                     1629 |                 155 |
| capital_50000000_participation_10pct | P1_broad_canonical        |             5e+07   |                 0.1  |                  0.275737 |                 0.27617  |                     2800 |                 158 |
| capital_50000000_participation_10pct | P2_conservative_consensus |             5e+07   |                 0.1  |                  0.241596 |                 0.240396 |                     2414 |                 158 |
| capital_50000000_participation_10pct | P4_kmi30_strict           |             5e+07   |                 0.1  |                  0.375339 |                 0.404829 |                      461 |                 135 |
| capital_50000000_participation_10pct | P5_shariah_screened       |             5e+07   |                 0.1  |                  0.350737 |                 0.344467 |                     1629 |                 155 |
| capital_50000000_participation_20pct | P1_broad_canonical        |             5e+07   |                 0.2  |                  0.372219 |                 0.379714 |                     2427 |                 158 |
| capital_50000000_participation_20pct | P2_conservative_consensus |             5e+07   |                 0.2  |                  0.328307 |                 0.331981 |                     2138 |                 158 |
| capital_50000000_participation_20pct | P4_kmi30_strict           |             5e+07   |                 0.2  |                  0.517615 |                 0.583718 |                      356 |                 128 |
| capital_50000000_participation_20pct | P5_shariah_screened       |             5e+07   |                 0.2  |                  0.432842 |                 0.459749 |                     1423 |                 149 |
| capital_50000000_participation_5pct  | P1_broad_canonical        |             5e+07   |                 0.05 |                  0.195292 |                 0.19248  |                     3111 |                 158 |
| capital_50000000_participation_5pct  | P2_conservative_consensus |             5e+07   |                 0.05 |                  0.164939 |                 0.16547  |                     2658 |                 158 |
| capital_50000000_participation_5pct  | P4_kmi30_strict           |             5e+07   |                 0.05 |                  0.258808 |                 0.241748 |                      547 |                 143 |
| capital_50000000_participation_5pct  | P5_shariah_screened       |             5e+07   |                 0.05 |                  0.271423 |                 0.243276 |                     1828 |                 155 |
| capital_5000000_participation_10pct  | P1_broad_canonical        |             5e+06   |                 0.1  |                  0.629591 |                 0.688703 |                     1432 |                 158 |
| capital_5000000_participation_10pct  | P2_conservative_consensus |             5e+06   |                 0.1  |                  0.566761 |                 0.633262 |                     1379 |                 158 |
| capital_5000000_participation_10pct  | P4_kmi30_strict           |             5e+06   |                 0.1  |                  0.795393 |                 0.869699 |                      151 |                  92 |
| capital_5000000_participation_10pct  | P5_shariah_screened       |             5e+06   |                 0.1  |                  0.683141 |                 0.794979 |                      795 |                 129 |
| capital_5000000_participation_20pct  | P1_broad_canonical        |             5e+06   |                 0.2  |                  0.750647 |                 0.821125 |                      964 |                 154 |
| capital_5000000_participation_20pct  | P2_conservative_consensus |             5e+06   |                 0.2  |                  0.701225 |                 0.778836 |                      951 |                 157 |
| capital_5000000_participation_20pct  | P4_kmi30_strict           |             5e+06   |                 0.2  |                  0.888889 |                 0.946524 |                       82 |                  59 |
| capital_5000000_participation_20pct  | P5_shariah_screened       |             5e+06   |                 0.2  |                  0.846951 |                 0.925725 |                      384 |                  99 |
| capital_5000000_participation_5pct   | P1_broad_canonical        |             5e+06   |                 0.05 |                  0.512675 |                 0.545234 |                     1884 |                 158 |
| capital_5000000_participation_5pct   | P2_conservative_consensus |             5e+06   |                 0.05 |                  0.455859 |                 0.488055 |                     1732 |                 158 |
| capital_5000000_participation_5pct   | P4_kmi30_strict           |             5e+06   |                 0.05 |                  0.703252 |                 0.76818  |                      219 |                 108 |
| capital_5000000_participation_5pct   | P5_shariah_screened       |             5e+06   |                 0.05 |                  0.55839  |                 0.639728 |                     1108 |                 141 |

## Implied policy capacity limits

| policy_id                 |   participation_rate |   trade_count |   minimum_supported_capital |   capital_99pct_trades_feasible |   capital_95pct_trades_feasible |   capital_90pct_trades_feasible |   median_supported_capital |
|:--------------------------|---------------------:|--------------:|----------------------------:|--------------------------------:|--------------------------------:|--------------------------------:|---------------------------:|
| P1_broad_canonical        |                 0.05 |          3866 |                     13969.1 |                170250           |                349332           |                526621           |                5.52551e+06 |
| P2_conservative_consensus |                 0.05 |          3183 |                     19104.3 |                133807           |                264590           |                427009           |                3.7383e+06  |
| P4_kmi30_strict           |                 0.05 |           738 |                    135388   |                417725           |                710837           |                     1.17062e+06 |                1.31795e+07 |
| P5_shariah_screened       |                 0.05 |          2509 |                    156553   |                418090           |                709197           |                980747           |                7.62418e+06 |
| P1_broad_canonical        |                 0.1  |          3866 |                     27938.2 |                340500           |                698664           |                     1.05324e+06 |                1.1051e+07  |
| P2_conservative_consensus |                 0.1  |          3183 |                     38208.5 |                267614           |                529181           |                854018           |                7.47659e+06 |
| P4_kmi30_strict           |                 0.1  |           738 |                    270777   |                835450           |                     1.42167e+06 |                     2.34125e+06 |                2.6359e+07  |
| P5_shariah_screened       |                 0.1  |          2509 |                    313107   |                836181           |                     1.41839e+06 |                     1.96149e+06 |                1.52484e+07 |
| P1_broad_canonical        |                 0.2  |          3866 |                     55876.4 |                681000           |                     1.39733e+06 |                     2.10648e+06 |                2.21021e+07 |
| P2_conservative_consensus |                 0.2  |          3183 |                     76417.1 |                535227           |                     1.05836e+06 |                     1.70804e+06 |                1.49532e+07 |
| P4_kmi30_strict           |                 0.2  |           738 |                    541554   |                     1.6709e+06  |                     2.84335e+06 |                     4.6825e+06  |                5.2718e+07  |
| P5_shariah_screened       |                 0.2  |          2509 |                    626213   |                     1.67236e+06 |                     2.83679e+06 |                     3.92299e+06 |                3.04967e+07 |

## Outputs

- Trade diagnostics: `data/processed/c10/capacity_trade_diagnostics.parquet`
- Scenario summary: `data/processed/c10/capacity_summary.parquet`
- Capacity limits: `data/processed/c10/capacity_limits.parquet`
