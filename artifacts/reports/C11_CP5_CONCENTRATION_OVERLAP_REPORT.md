# C11 CP5 — Concentration and Overlap

## Scope

CP5 is diagnostic only. It does not train models, alter selections or optimize
allocation weights.

It measures target concentration on weekly signal dates, realized daily close
concentration after execution, name/sector HHI and effective counts, and
pairwise source-policy selection overlap.

Realized name/sector concentration is normalized over invested capital, so
residual cash cannot make a concentrated invested portfolio look safer.

## Focus allocations at PKR 1,000,000

| allocation_id       |   target_names_median |   target_max_name_mean |   target_max_name_worst |   target_top3_mean |   target_effective_names_mean |   target_max_sector_mean |   target_max_sector_worst |   realized_max_name_mean |   realized_max_name_worst |   realized_top3_mean |   realized_effective_names_mean |   realized_effective_names_min |   realized_max_sector_mean |   realized_max_sector_worst |   realized_effective_sectors_mean |
|:--------------------|----------------------:|-----------------------:|------------------------:|-------------------:|------------------------------:|-------------------------:|--------------------------:|-------------------------:|--------------------------:|---------------------:|--------------------------------:|-------------------------------:|---------------------------:|----------------------------:|----------------------------------:|
| A05_P4              |                     3 |               0.333333 |                0.333333 |           1        |                       3       |                 0.403397 |                  0.666667 |                 0.349106 |                  1        |             1        |                         2.9765  |                        1       |                   0.414475 |                    1        |                           2.73798 |
| A06_P5              |                    10 |               0.106506 |                0.142857 |           0.319517 |                       9.87261 |                 0.207837 |                  0.285714 |                 0.118167 |                  0.508214 |             0.340995 |                         9.69822 |                        1.99946 |                   0.215486 |                    0.508214 |                           7.11717 |
| A07_P4_25_P5_75     |                    11 |               0.146319 |                0.190476 |           0.377702 |                      10.4939  |                 0.22709  |                  0.380952 |                 0.152844 |                  0.383947 |             0.3901   |                        10.285   |                        2.96561 |                   0.230814 |                    0.455081 |                           7.14113 |
| A16_P2F_P4_P5_equal |                    17 |               0.148082 |                0.333333 |           0.399975 |                      12.5958  |                 0.226107 |                  0.372222 |                 0.154695 |                  0.653683 |             0.407459 |                        12.3754  |                        2.05222 |                   0.230332 |                    0.653683 |                           7.86741 |
| A17_P2R_P4_P5_equal |                    18 |               0.147196 |                0.333333 |           0.399816 |                      12.8437  |                 0.224972 |                  0.362963 |                 0.154041 |                  0.652724 |             0.407185 |                        12.6217  |                        2.05611 |                   0.229062 |                    0.652724 |                           7.93302 |

## Source-policy overlap

| left_policy         | right_policy          |   dates |   intersection_mean |   intersection_median |   jaccard_mean |   jaccard_median |   jaccard_max |   left_overlap_mean |   right_overlap_mean |
|:--------------------|:----------------------|--------:|--------------------:|----------------------:|---------------:|-----------------:|--------------:|--------------------:|---------------------:|
| D_P2_shariah_filter | D_P2_shariah_refill   |     157 |            7.46497  |                     7 |      0.912966  |         0.923077 |      1        |           0.999292  |            0.913532  |
| D_P1_shariah_filter | D_P2_shariah_filter   |     157 |            7.38854  |                     7 |      0.783861  |         0.818182 |      1        |           0.789204  |            0.989657  |
| D_P1_shariah_filter | D_P2_shariah_refill   |     157 |            7.38217  |                     7 |      0.722069  |         0.727273 |      1        |           0.788625  |            0.903801  |
| D_P1_shariah_filter | D_P1_shariah_refill   |     157 |            9.35032  |                     9 |      0.572479  |         0.5625   |      0.923077 |           0.998713  |            0.573528  |
| D_P1_shariah_refill | D_P2_shariah_refill   |     157 |            8.15924  |                     8 |      0.490961  |         0.5      |      0.818182 |           0.49279   |            0.992174  |
| D_P1_shariah_refill | D_P2_shariah_filter   |     157 |            7.41401  |                     7 |      0.447403  |         0.4375   |      0.818182 |           0.448903  |            0.99339   |
| D_P4_kmi30_strict   | D_P5_shariah_screened |     157 |            1.48408  |                     1 |      0.150107  |         0.111111 |      0.428571 |           0.494692  |            0.161486  |
| D_P1_shariah_refill | D_P5_shariah_screened |     157 |            1.44586  |                     1 |      0.0644334 |         0.04     |      0.45     |           0.089587  |            0.146308  |
| D_P1_shariah_filter | D_P5_shariah_screened |     157 |            0.898089 |                     0 |      0.0536129 |         0        |      0.466667 |           0.0944057 |            0.090872  |
| D_P2_shariah_refill | D_P5_shariah_screened |     157 |            0.738854 |                     0 |      0.0476891 |         0        |      0.571429 |           0.0909175 |            0.0734632 |
| D_P2_shariah_filter | D_P5_shariah_screened |     157 |            0.687898 |                     0 |      0.0459141 |         0        |      0.571429 |           0.094378  |            0.0683548 |
| D_P1_shariah_refill | D_P4_kmi30_strict     |     157 |            0.515924 |                     0 |      0.0301089 |         0        |      0.214286 |           0.0328694 |            0.171975  |
| D_P1_shariah_filter | D_P4_kmi30_strict     |     157 |            0.324841 |                     0 |      0.0293245 |         0        |      0.222222 |           0.0353415 |            0.10828   |
| D_P2_shariah_refill | D_P4_kmi30_strict     |     157 |            0.261146 |                     0 |      0.0259526 |         0        |      0.25     |           0.0318202 |            0.0870488 |
| D_P2_shariah_filter | D_P4_kmi30_strict     |     157 |            0.235669 |                     0 |      0.0249131 |         0        |      0.25     |           0.0319435 |            0.0785563 |

## Interpretation

High historical return does not excuse poor diversification. Compare worst
single-name weight, top-3 concentration, effective names, sector concentration
and source-policy overlap before choosing the final deployment allocation.

P1 remains diagnostic because CP4A materially transformed it under refill.
The primary comparison remains P4, P5, P4/P5 and the two P2/P4/P5 equal-third
candidates.
