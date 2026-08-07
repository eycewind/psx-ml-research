# C10 Checkpoint 2 Ledger Audit

Status: **PASS**

## Accounting integrity

- Trade rows: 7,049
- Position rows: 22,235
- NAV rows: 1,482
- Holdout rows: 0
- Maximum NAV identity error: 0
- Maximum position-to-NAV reconciliation error: 4.66e-10
- Duplicate trade keys: 0
- Duplicate position keys: 0
- Duplicate NAV keys: 0
- Trades executed on or before signal date: 0
- Future valuation marks: 0
- Extreme absolute daily returns above 10%: 0

## Deferred exits

SHSML had no valid adjusted opening price on 2023-10-24.

For both P1 and P2:

- intended exit date: 2023-10-24
- actual exit date: 2023-10-25
- actual adjusted opening price: 194.85
- treatment: deferred exit at first later valid open

No future opening price was used on the blocked date.

## Stale valuations

- P1 stale position-days: 18
- P2 stale position-days: 15
- Maximum stale interval: 3 calendar days
- Future valuation marks: 0

Missing daily closes were valued using only the latest available prior adjusted close.

## Cash and invested weight

Maximum cash balances:

- P1: PKR 84,267.41
- P2: PKR 90,880.60

Minimum invested position-weight sum: 0.920680.

The difference from 1.0 represents cash. Deferred-exit proceeds remain in cash until the next scheduled weekly rebalance. They are not reinvested through an unscheduled midweek rebalance.

## Return reconciliation

- P1 compounded return multiplier: 4.811354800964437
- P1 ending-NAV multiplier: 4.811354800964431
- Difference: 6.22e-15

- P2 compounded return multiplier: 5.030558842194135
- P2 ending-NAV multiplier: 5.030558842194133
- Difference: 1.78e-15

## Interpretation

Checkpoint 2 is a frictionless accounting baseline. It permits fractional shares and excludes fees, taxes, spread, slippage, market impact, board lots and capacity restrictions.

The gross annualized performance must not be interpreted as realizable performance until later C10 checkpoints apply those constraints.
