# C10 CP4A P4 KMI-30 Selection Report

## Policy

- Policy ID: `P4_kmi30_strict`
- Prediction basis: accepted C8 out-of-fold LightGBM
- Target: 5-session market-relative rank
- Feature variant: `B_market_context`
- Schedule: P1 weekly signal dates
- Universe: point-in-time KMI-30 only
- Selection: top 10% within effective KMI-30 candidates
- Sector cap: maximum 2 selected names per sector
- Ties: prediction descending, symbol ascending
- Retraining: none
- 2026 holdout accessed: false

## Summary

| metric            | value      |
|:------------------|:-----------|
| rows              | 471        |
| signal_dates      | 157        |
| unique_symbols    | 51         |
| minimum_holdings  | 3          |
| median_holdings   | 3.0        |
| maximum_holdings  | 3          |
| first_signal_date | 2023-01-02 |
| last_signal_date  | 2025-12-29 |

## Membership interval coverage

| effective_from      | effective_to   |   selection_rows |   signal_dates |   selected_symbols |
|:--------------------|:---------------|-----------------:|---------------:|-------------------:|
| 2022-12-30 00:00:00 | 2023-07-06     |               81 |             27 |                 14 |
| 2023-07-07 00:00:00 | 2024-06-13     |              147 |             49 |                 24 |
| 2024-06-14 00:00:00 | 2024-12-29     |               84 |             28 |                 23 |
| 2024-12-30 00:00:00 | 2025-06-01     |               66 |             22 |                 24 |
| 2025-06-02 00:00:00 | 2025-11-23     |               75 |             25 |                 21 |
| 2025-11-24 00:00:00 | 9999-12-31     |               18 |              6 |                 15 |
