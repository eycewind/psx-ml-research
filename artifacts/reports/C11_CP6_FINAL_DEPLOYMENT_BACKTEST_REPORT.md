# C11 CP6 — Final Deployment Backtest

## Decision

**Primary deployment allocation: `A07_P4_25_P5_75`**

Composition:

- 25% sleeve allocation to `D_P4_kmi30_strict`
- 75% sleeve allocation to `D_P5_shariah_screened`
- each sleeve equal-weight internally on each signal date;
- overlapping symbols merged into one target position/order.

**Secondary diagnostic candidate: `A17_P2R_P4_P5_equal`**

`A06_P5` remains the standalone Shariah-screened benchmark.

## Why A07 is frozen as primary

This is not a return-maximizing grid search. CP4B defined the candidate weights
before evaluation and CP5 assessed concentration separately.

Compared with A17, A07:

- uses only the two native Shariah deployment policies P4 and P5;
- avoids dependency on the materially transformed P2-refill sleeve;
- has substantially lower worst realized single-name concentration;
- has substantially lower worst realized sector concentration;
- retains strong execution characteristics;
- produced higher historical annualized return in the accepted pre-holdout test.

A17 remains useful as a risk-balanced diagnostic because its historical Sharpe
and maximum drawdown were somewhat better.

## PKR 1,000,000 finalist comparison

| allocation_id       |   ending_nav |   annualized_return |   sharpe_zero_rf |   max_drawdown |   buy_fill_fraction |   mean_cash_fraction |   total_transaction_cost |   realized_max_name_worst |   realized_max_sector_worst |   realized_effective_names_mean |
|:--------------------|-------------:|--------------------:|-----------------:|---------------:|--------------------:|---------------------:|-------------------------:|--------------------------:|----------------------------:|--------------------------------:|
| A06_P5              |  3.58467e+06 |            0.53208  |          1.62292 |      -0.217578 |            0.972376 |            0.0159927 |              1.26298e+06 |                  0.508214 |                    0.508214 |                         9.69822 |
| A07_P4_25_P5_75     |  3.61632e+06 |            0.536587 |          1.66592 |      -0.209292 |            0.975912 |            0.0136501 |              1.20425e+06 |                  0.383947 |                    0.455081 |                        10.285   |
| A17_P2R_P4_P5_equal |  3.05971e+06 |            0.453118 |          1.68251 |      -0.17679  |            0.981342 |            0.0126636 |         825789           |                  0.652724 |                    0.652724 |                        12.6217  |

## Stability across capital levels

| allocation_id       |   capital_levels |   annualized_return_min |   annualized_return_max |   sharpe_min |   sharpe_max |   max_drawdown_worst |   buy_fill_fraction_min |   mean_cash_fraction_max |   ending_nav_1m |
|:--------------------|-----------------:|------------------------:|------------------------:|-------------:|-------------:|---------------------:|------------------------:|-------------------------:|----------------:|
| A06_P5              |                5 |                0.531215 |                0.532187 |      1.62292 |      1.62585 |            -0.217578 |                0.972222 |                0.0196575 |     3.58467e+06 |
| A07_P4_25_P5_75     |                5 |                0.53467  |                0.536597 |      1.66589 |      1.66711 |            -0.209292 |                0.974448 |                0.0182653 |     3.61632e+06 |
| A17_P2R_P4_P5_equal |                5 |                0.43652  |                0.453118 |      1.65591 |      1.68326 |            -0.17679  |                0.981098 |                0.0450705 |     3.05971e+06 |

## Frozen execution semantics

No execution rule is changed in CP6. The final backtest is an exact extraction
from the accepted CP4B merged-portfolio execution ledger:

- BUY limit = signal-session close +2%;
- next session only;
- fill at open if open <= limit;
- otherwise intraday-touch proxy at limit if low <= limit;
- otherwise miss/no chase;
- whole shares;
- exact broker costs;
- no leverage;
- next-open reductions/exits with deferred exits when required.

## Shariah semantics

A07 inherits the accepted CP4A policy rules:

- P4: official PIT KMI30 membership is authoritative Shariah provenance;
- P5: PIT screened-universe eligibility is mandatory;
- no unknown/non-eligible row is executable.

## Holdout

No 2026 data is accessed. CP6 does not retrain, re-rank, change selections,
search weights, or introduce new indicators.

## Next checkpoint

CP7 converts the frozen A07 policy into a production signal/order artifact for
the next live session, including capital-aware whole-share orders, limits,
Shariah provenance and explicit skip/miss reasons.
