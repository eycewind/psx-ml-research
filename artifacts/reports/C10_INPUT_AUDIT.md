# C10 Input Audit

## Frozen policies

```json
{
  "P1_broad_canonical": {
    "policy_id": "P1_broad_canonical",
    "models": [
      "lightgbm_cpu"
    ],
    "target": "fwd_market_relative_rank_5s",
    "feature_variant": "B_market_context",
    "selection": "top_10pct",
    "rebalance": "weekly_first_session",
    "sector_cap": 2,
    "liquidity_screen": "L0"
  },
  "P2_conservative_consensus": {
    "policy_id": "P2_conservative_consensus",
    "models": [
      "lightgbm_cpu",
      "xgboost_gpu"
    ],
    "target": "fwd_market_relative_rank_5s",
    "feature_variant": "B_market_context",
    "selection": "intersection_top_10pct",
    "rebalance": "weekly_first_session",
    "sector_cap": 2,
    "liquidity_screen": "L1"
  }
}
```

## C9 selections

- Path: `data/processed/c9/candidate_selections.parquet`
- Rows: `4696`
- Symbols: `249`
- Minimum date: `2023-01-02`
- Maximum date: `2025-12-29`
- Holdout rows: `0`
- Duplicate date-symbol keys: `0`

## Liquidity features

- Path: `data/processed/features/daily_features.parquet`
- Rows: `557346`
- Symbols: `778`
- Minimum date: `2020-01-01`
- Maximum date: `2025-12-29`
- Holdout rows: `0`
- Duplicate date-symbol keys: `0`

The 2026 final holdout remained inaccessible.
