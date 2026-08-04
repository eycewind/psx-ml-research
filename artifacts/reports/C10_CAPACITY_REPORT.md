# C10 Liquidity and Capacity Report

## Scope

Checkpoint 4 measures whether the frozen P1 and P2 trade ledgers can be executed at larger portfolio sizes.

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
| capital_10000000_participation_20pct | P1_broad_canonical        |             1e+07   |                 0.2  |                  0.629591 |                 0.688703 |                     1432 |                 158 |
| capital_10000000_participation_20pct | P2_conservative_consensus |             1e+07   |                 0.2  |                  0.566761 |                 0.633262 |                     1379 |                 158 |
| capital_10000000_participation_5pct  | P1_broad_canonical        |             1e+07   |                 0.05 |                  0.403777 |                 0.417096 |                     2305 |                 158 |
| capital_10000000_participation_5pct  | P2_conservative_consensus |             1e+07   |                 0.05 |                  0.35721  |                 0.366019 |                     2046 |                 158 |
| capital_1000000_participation_10pct  | P1_broad_canonical        |             1e+06   |                 0.1  |                  0.908691 |                 0.946349 |                      353 |                 127 |
| capital_1000000_participation_10pct  | P2_conservative_consensus |             1e+06   |                 0.1  |                  0.872133 |                 0.923763 |                      407 |                 135 |
| capital_1000000_participation_20pct  | P1_broad_canonical        |             1e+06   |                 0.2  |                  0.973099 |                 0.98653  |                      104 |                  65 |
| capital_1000000_participation_20pct  | P2_conservative_consensus |             1e+06   |                 0.2  |                  0.957901 |                 0.977921 |                      134 |                  79 |
| capital_1000000_participation_5pct   | P1_broad_canonical        |             1e+06   |                 0.05 |                  0.797724 |                 0.857926 |                      782 |                 152 |
| capital_1000000_participation_5pct   | P2_conservative_consensus |             1e+06   |                 0.05 |                  0.744581 |                 0.820167 |                      813 |                 156 |
| capital_25000000_participation_10pct | P1_broad_canonical        |             2.5e+07 |                 0.1  |                  0.372219 |                 0.379714 |                     2427 |                 158 |
| capital_25000000_participation_10pct | P2_conservative_consensus |             2.5e+07 |                 0.1  |                  0.328307 |                 0.331981 |                     2138 |                 158 |
| capital_25000000_participation_20pct | P1_broad_canonical        |             2.5e+07 |                 0.2  |                  0.480859 |                 0.502279 |                     2007 |                 158 |
| capital_25000000_participation_20pct | P2_conservative_consensus |             2.5e+07 |                 0.2  |                  0.422872 |                 0.446229 |                     1837 |                 158 |
| capital_25000000_participation_5pct  | P1_broad_canonical        |             2.5e+07 |                 0.05 |                  0.275737 |                 0.27617  |                     2800 |                 158 |
| capital_25000000_participation_5pct  | P2_conservative_consensus |             2.5e+07 |                 0.05 |                  0.241596 |                 0.240396 |                     2414 |                 158 |
| capital_50000000_participation_10pct | P1_broad_canonical        |             5e+07   |                 0.1  |                  0.275737 |                 0.27617  |                     2800 |                 158 |
| capital_50000000_participation_10pct | P2_conservative_consensus |             5e+07   |                 0.1  |                  0.241596 |                 0.240396 |                     2414 |                 158 |
| capital_50000000_participation_20pct | P1_broad_canonical        |             5e+07   |                 0.2  |                  0.372219 |                 0.379714 |                     2427 |                 158 |
| capital_50000000_participation_20pct | P2_conservative_consensus |             5e+07   |                 0.2  |                  0.328307 |                 0.331981 |                     2138 |                 158 |
| capital_50000000_participation_5pct  | P1_broad_canonical        |             5e+07   |                 0.05 |                  0.195292 |                 0.19248  |                     3111 |                 158 |
| capital_50000000_participation_5pct  | P2_conservative_consensus |             5e+07   |                 0.05 |                  0.164939 |                 0.16547  |                     2658 |                 158 |
| capital_5000000_participation_10pct  | P1_broad_canonical        |             5e+06   |                 0.1  |                  0.629591 |                 0.688703 |                     1432 |                 158 |
| capital_5000000_participation_10pct  | P2_conservative_consensus |             5e+06   |                 0.1  |                  0.566761 |                 0.633262 |                     1379 |                 158 |
| capital_5000000_participation_20pct  | P1_broad_canonical        |             5e+06   |                 0.2  |                  0.750647 |                 0.821125 |                      964 |                 154 |
| capital_5000000_participation_20pct  | P2_conservative_consensus |             5e+06   |                 0.2  |                  0.701225 |                 0.778836 |                      951 |                 157 |
| capital_5000000_participation_5pct   | P1_broad_canonical        |             5e+06   |                 0.05 |                  0.512675 |                 0.545234 |                     1884 |                 158 |
| capital_5000000_participation_5pct   | P2_conservative_consensus |             5e+06   |                 0.05 |                  0.455859 |                 0.488055 |                     1732 |                 158 |

## Implied policy capacity limits

| policy_id                 |   participation_rate |   trade_count |   minimum_supported_capital |   capital_99pct_trades_feasible |   capital_95pct_trades_feasible |   capital_90pct_trades_feasible |   median_supported_capital |
|:--------------------------|---------------------:|--------------:|----------------------------:|--------------------------------:|--------------------------------:|--------------------------------:|---------------------------:|
| P1_broad_canonical        |                 0.05 |          3866 |                     13969.1 |                          170250 |                349332           |                526621           |                5.52551e+06 |
| P2_conservative_consensus |                 0.05 |          3183 |                     19104.3 |                          133807 |                264590           |                427009           |                3.7383e+06  |
| P1_broad_canonical        |                 0.1  |          3866 |                     27938.2 |                          340500 |                698664           |                     1.05324e+06 |                1.1051e+07  |
| P2_conservative_consensus |                 0.1  |          3183 |                     38208.5 |                          267614 |                529181           |                854018           |                7.47659e+06 |
| P1_broad_canonical        |                 0.2  |          3866 |                     55876.4 |                          681000 |                     1.39733e+06 |                     2.10648e+06 |                2.21021e+07 |
| P2_conservative_consensus |                 0.2  |          3183 |                     76417.1 |                          535227 |                     1.05836e+06 |                     1.70804e+06 |                1.49532e+07 |

## Outputs

- Trade diagnostics: `data/processed/c10/capacity_trade_diagnostics.parquet`
- Scenario summary: `data/processed/c10/capacity_summary.parquet`
- Capacity limits: `data/processed/c10/capacity_limits.parquet`
