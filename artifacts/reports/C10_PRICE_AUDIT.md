# C10 Price Audit

## Source

- Path: `data/cache/daily_ohlcv.parquet`
- Rows loaded after holdout restriction: `557346`
- Symbols: `778`
- Minimum date: `2020-01-01`
- Maximum date: `2025-12-29`
- Holdout rows: `0`
- Duplicate date-symbol keys: `0`

## Canonical price basis

- Entry: next valid market session `open_adj`
- Daily valuation: `close_adj`
- Volume: `volume_adj`
- Adjustment identity: `adj_factor`

Raw and adjusted OHLC columns both exist in the source, but C10 uses the adjusted basis consistently.

## Entry availability

| policy_id                 |   selection_rows |   available_entries |   missing_entries |   selection_dates |   symbols |   availability_rate |
|:--------------------------|-----------------:|--------------------:|------------------:|------------------:|----------:|--------------------:|
| P1_broad_canonical        |             2576 |                2555 |                21 |               157 |       249 |            0.991848 |
| P2_conservative_consensus |             2120 |                2102 |                18 |               157 |       231 |            0.991509 |

## Missing-entry reasons

| policy_id                 | entry_missing_reason   |   rows |
|:--------------------------|:-----------------------|-------:|
| P1_broad_canonical        | no_next_market_session |     21 |
| P2_conservative_consensus | no_next_market_session |     18 |
