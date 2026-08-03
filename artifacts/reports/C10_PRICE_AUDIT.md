# C10 Price Audit

## Source

- Path: `data/cache/daily_ohlcv.parquet`
- Rows loaded after holdout restriction: `558325`
- Symbols: `780`
- Minimum date: `2020-01-01`
- Maximum date: `2025-12-31`
- Holdout rows: `0`
- Duplicate date/symbol keys: `0`

## Canonical price basis

- Entry: next valid market session `open_adj`
- Daily valuation: `close_adj`
- Volume: `volume_adj`
- Adjustment identity: `adj_factor`

Raw and adjusted OHLC columns both exist in the source, but C10 uses the adjusted basis consistently.

## Entry availability

| policy_id                 |   selection_rows |   available_entries |   missing_entries |   selection_dates |   symbols |   availability_rate |
|:--------------------------|-----------------:|--------------------:|------------------:|------------------:|----------:|--------------------:|
| P1_broad_canonical        |             2576 |                2576 |                 0 |               157 |       249 |                   1 |
| P2_conservative_consensus |             2120 |                2120 |                 0 |               157 |       231 |                   1 |

## Missing-entry reasons

No missing entries.
