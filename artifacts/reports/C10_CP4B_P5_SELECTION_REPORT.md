# C10 CP4B — P5 Selection Report

- Policy: `P5_shariah_screened`
- Universe: point-in-time official Shariah-screened universe
- Exact KMI All Share membership claimed: no
- Model: `lightgbm_cpu`
- Horizon: `5`
- Target family: `market_relative`
- Feature variant: `B_market_context`
- Liquidity: exclude bottom 25% by `turnover_median_20obs_adj`
- Selection: top 10% after liquidity filter
- Sector cap: 2

## Counts

- Rows: 1550
- Signal dates: 157
- Unique symbols: 173
- Date range: 2023-01-02 to 2025-12-29
- Holdings/date min: 7
- Holdings/date median: 10.0
- Holdings/date max: 15
- Selection shortfall dates: 0

## Membership confidence exposure

| Confidence | Rows | Signal dates | Unique symbols |
|---|---:|---:|---:|
| low | 560 | 52 | 120 |
| medium | 990 | 105 | 157 |
