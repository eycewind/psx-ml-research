# C6 Universe Report

All variants require the unchanged same-date C1 PIT liquidity flag. Classification exclusions are separate from liquidity and history exclusions; targets, predictions, returns, and residuals are not inputs.

## Eligible row counts

```json
{
  "pit_liquid_all_instruments_v1": 305267,
  "pit_liquid_equity_like_v1": 302675,
  "pit_liquid_ordinary_equity_v1": 300808
}
```

## C7 recommendation

Recommend `pit_liquid_ordinary_equity_v1` as the canonical C7 research universe. The rule is structural and target/residual-independent, retains 300,808 of 305,267 PIT-liquid rows, and excludes fixed income, rights, ETFs, REITs, and other non-ordinary families. Lower RMSE alone is not the justification.

The 2026-08-01 security master is current-state evidence; historical assignments from it are explicit backcasts. Historical symbols absent from it use observed-sector evidence or labeled low-confidence fallbacks.
