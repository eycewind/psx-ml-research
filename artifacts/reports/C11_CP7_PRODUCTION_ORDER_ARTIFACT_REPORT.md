# C11 CP7 — Production Signal / Order Artifact

## Frozen production policy

`A07_P4_25_P5_75`

- 25% `D_P4_kmi30_strict`
- 75% `D_P5_shariah_screened`
- equal weight inside each sleeve
- overlapping names merged
- hard Shariah provenance
- BUY limit = signal close +2%
- next session only
- no chase
- whole shares and exact broker fees at execution

## Two-phase live workflow

CP7 deliberately separates **signal planning** from **session-open sizing**.

### Phase A — after signal-session close

`build_signal_plan(...)` produces:

- merged A07 target weights;
- P4/P5 contribution flags;
- Shariah provenance/confidence;
- signal close;
- +2% BUY limit;
- explicit `DEFER_TO_SESSION_OPEN` sizing status.

Exact target shares are **not** fabricated after the close because the accepted
CP3/CP4B sizing rule uses the next session's actual opening prices.

### Phase B — next session open

`build_session_open_orders(...)` receives:

- the frozen signal plan;
- actual session opens;
- current positions;
- available cash.

It then produces exact whole-share BUY/SELL/HOLD actions. SELL reductions are
resolved first. BUYs whose open is within the +2% limit are ready at the open;
BUYs opening above the limit become DAY limit orders waiting for the accepted
intraday-touch condition.

The live engine never needs to retrain or alter the accepted policy.

## Acceptance fixture

CP7 acceptance uses only historical pre-holdout data.

Fixture signal date: `2025-12-22`

Rows: 17

Target weight sum: 1.000000000000

No 2026/live data is consumed by this checkpoint.

## Production output schema

Signal-plan fields include:

- `allocation_id`
- `trade_date`
- `symbol`
- `p4_selected`
- `p5_selected`
- `target_weight`
- `contributing_policies`
- `shariah_eligible`
- `shariah_sources`
- `shariah_confidences`
- `signal_close`
- `buy_limit_price`
- `execution_rule`
- `sizing_status`
- `status`
- `reason`

Session-open order fields include:

- `signal_date`
- `execution_date`
- `symbol`
- `target_weight`
- `current_shares`
- `target_shares`
- `order_side`
- `order_shares`
- `order_type`
- `reference_open`
- `buy_limit_price`
- estimated broker fee components
- `status`
- `reason`

## Boundary

This checkpoint constructs orders from supplied current selections/prices.
It does **not** define how the production system obtains a new 2026 P4/P5
selection. That live ranking/screening integration must feed the same frozen
input schema and is operational wiring rather than a new trading methodology.
