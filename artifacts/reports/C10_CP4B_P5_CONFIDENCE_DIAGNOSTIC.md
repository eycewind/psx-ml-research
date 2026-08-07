# C10 CP4B — P5 Membership-Confidence Diagnostic

- Policy: `P5_shariah_screened`
- Net cost schedule: `actual_broker_all_in`
- Holdout accessed: no
- Purpose: diagnose whether P5 performance is concentrated in low-confidence carried-forward screening periods.
- Important: these are confidence-conditioned return streams, not independent re-run portfolios.
- The 252-session conditioned annualized return is a diagnostic normalization, not the official C10 calendar CAGR.
- The conditioned-stream drawdown is measured after filtering to a confidence subset and is not a continuous live-portfolio drawdown.

## Selection exposure

| Confidence | Selection rows | Signal dates | Unique symbols |
|---|---:|---:|---:|
| low | 560 | 52 | 120 |
| medium | 990 | 105 | 157 |

## Return-stream sensitivity

| Stream | Confidence | Days | Conditioned total return | 252-session conditioned annualized return | Ann. vol | Sharpe | Conditioned-stream max drawdown | Positive days |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| frictionless | all | 741 | 557.60% | 89.75% | 30.10% | 2.280 | -17.84% | 56.41% |
| actual_broker_all_in | all | 741 | 261.09% | 54.75% | 30.22% | 1.597 | -22.86% | 55.06% |
| frictionless | medium | 487 | 206.69% | 78.59% | 30.41% | 2.060 | -16.44% | 55.03% |
| actual_broker_all_in | medium | 487 | 103.43% | 44.41% | 30.53% | 1.356 | -22.86% | 53.80% |
| frictionless | low | 254 | 114.41% | 113.13% | 29.56% | 2.711 | -25.82% | 59.06% |
| actual_broker_all_in | low | 254 | 77.50% | 76.70% | 29.65% | 2.070 | -26.59% | 57.48% |

## Transaction-cost attribution

| Confidence | Days | Trade count | Traded notional | Transaction cost | Weighted cost rate |
|---|---:|---:|---:|---:|---:|
| low | 254 | 857 | 225,078,372.21 | 728,565.71 | 0.32% |
| medium | 487 | 1652 | 401,613,736.58 | 1,129,792.50 | 0.28% |

## Interpretation

P5 passes the source-quality sensitivity check if medium-confidence periods retain materially positive net performance and low-confidence periods are not the sole source of strategy performance. Divergence between confidence groups should be recorded as source-quality sensitivity and must not be used to alter the frozen P5 policy.
