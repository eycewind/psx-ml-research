# C11 CP4A — PIT Shariah-Gated Deployment Selections

## Status

Selection transformation complete. This stage does **not** choose policy weights or a final deployment combination.

## Frozen rule

- Every executable candidate must pass the accepted point-in-time Shariah gate.
- Unknown/unavailable eligibility is rejected.
- Low-confidence eligible rows remain allowed and are flagged.
- P1/P2 accepted C9 outputs remain immutable.
- `filter_only` removes rejected names without replacement.
- `filter_and_refill` scans the original accepted ranking and preserves the upstream selected holding count where possible.
- P1 refill may continue below the original top-10% cut because CP1 explicitly defines refill as a deployment transformation that continues down the accepted ranking.
- P2 refill does **not** broaden the accepted consensus definition. It scans only the original P2 top-10% LightGBM/XGBoost consensus intersection, in the same LightGBM percentile-rank order used by the accepted S1 sector constraint. Therefore P2 refill may retain a shortfall when the accepted consensus pool contains too few PIT-Shariah-eligible names.
- P4 uses its official PIT KMI30 membership as authoritative Shariah provenance; the generic screened history is secondary diagnostic coverage and cannot veto a valid KMI30 row.
- P5 is defensively re-gated against the accepted screened-universe history.

## Exact C9 reconstruction

- P1 reconstructed before gating: **PASS**
- P2 reconstructed before gating: **PASS**
- C9 accepted selection artifact unchanged: **PASS**
- 2026 holdout accessed: **false**

## Deployment selection summary

| policy_id             |   rows |   dates |   symbols |   holdings_min |   holdings_median |   holdings_max |   gate_rejections_in_audit |   unknown_rejections_in_audit |   low_confidence_selected_rows |   refill_selected_rows |   shortfall_dates |
|:----------------------|-------:|--------:|----------:|---------------:|------------------:|---------------:|---------------------------:|------------------------------:|-------------------------------:|-----------------------:|------------------:|
| D_P1_shariah_filter   |   1470 |     157 |       166 |              4 |                 9 |             22 |                       1106 |                          1106 |                            548 |                      0 |                 0 |
| D_P1_shariah_refill   |   2576 |     157 |       190 |              9 |                16 |             27 |                      11490 |                         11490 |                            946 |                   1108 |                 0 |
| D_P2_shariah_filter   |   1173 |     157 |       153 |              1 |                 7 |             19 |                        947 |                           947 |                            461 |                      0 |                 0 |
| D_P2_shariah_refill   |   1292 |     157 |       162 |              1 |                 8 |             20 |                       1161 |                          1161 |                            507 |                    120 |               153 |
| D_P4_kmi30_strict     |    471 |     157 |        51 |              3 |                 3 |              3 |                          0 |                             0 |                              0 |                      0 |                 0 |
| D_P5_shariah_screened |   1550 |     157 |       173 |              7 |                10 |             15 |                          0 |                             0 |                            560 |                      0 |                 0 |

## Holding shortfalls versus accepted upstream P1/P2

```json
{
  "D_P1_shariah_filter": {
    "dates": 155,
    "total_missing_holdings": 1106,
    "maximum_shortfall": 12
  },
  "D_P1_shariah_refill": {
    "dates": 0,
    "total_missing_holdings": 0,
    "maximum_shortfall": 0
  },
  "D_P2_shariah_filter": {
    "dates": 153,
    "total_missing_holdings": 947,
    "maximum_shortfall": 11
  },
  "D_P2_shariah_refill": {
    "dates": 153,
    "total_missing_holdings": 828,
    "maximum_shortfall": 11
  }
}
```

## Interpretation boundary

CP4A establishes auditable Shariah-compliant deployment candidate sets only.
It does not select between filter-only and refill based on historical returns.
That decision belongs to the CP4 capital-allocation/execution comparison.

## Outputs

- `data/processed/c11/deployment_selections.parquet`
- `data/processed/c11/deployment_shariah_gate_audit.parquet`
